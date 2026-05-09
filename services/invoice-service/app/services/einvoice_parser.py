"""
Estonian e-invoice 1.2 and UBL 2.1 XML parsers.
Produces a dict that can be fed into the Invoice model.

Security note: all XML parsing uses a hardened lxml XMLParser with
  - resolve_entities=False  (prevents XXE / entity-expansion attacks)
  - no_network=True         (blocks external DTD/schema fetches)
  - huge_tree=False         (limits tree depth to prevent DoS)
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional
from lxml import etree


# ---------------------------------------------------------------------------
# Shared safe parser – used for every fromstring() call in this module.
# CVE addressed: lxml XXE via default iterparse()/ETCompatXMLParser()
# Fixed in lxml >= 6.1.0; this explicit configuration also prevents the
# vulnerability in earlier versions that may end up on the classpath.
# ---------------------------------------------------------------------------
_SAFE_PARSER = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    huge_tree=False,
)


def _safe_fromstring(xml_bytes: bytes) -> etree._Element:
    """Parse XML bytes using the hardened parser. Raises etree.XMLSyntaxError on bad input."""
    return etree.fromstring(xml_bytes, parser=_SAFE_PARSER)


# ──────────────────────────────────────────────
# Estonian e-invoice 1.2 parser
# ──────────────────────────────────────────────
_ET_NS = {
    "e": "http://www.estfatura.ee/xml/schemas/2019/01/EInvoice",
}


def _et_text(element, xpath: str, ns: dict = _ET_NS) -> Optional[str]:
    nodes = element.xpath(xpath, namespaces=ns)
    if nodes:
        value = nodes[0]
        if hasattr(value, "text"):
            return (value.text or "").strip() or None
        return (str(value)).strip() or None
    return None


def _et_decimal(element, xpath: str, ns: dict = _ET_NS) -> Optional[Decimal]:
    val = _et_text(element, xpath, ns)
    if val is not None:
        try:
            return Decimal(val)
        except Exception:
            pass
    return None


def _et_date(element, xpath: str, ns: dict = _ET_NS) -> Optional[date]:
    val = _et_text(element, xpath, ns)
    if val:
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y%m%d"):
            try:
                from datetime import datetime
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None


def parse_estonian_einvoice(xml_bytes: bytes) -> dict:
    """Parse Estonian e-invoice XML 1.2 into a normalised dict."""
    root = _safe_fromstring(xml_bytes)

    # Try with namespace, fall back to no-namespace parsing
    inv = root.xpath("//e:Invoice", namespaces=_ET_NS)
    if not inv:
        inv = root.xpath("//*[local-name()='Invoice']")
    inv = inv[0] if inv else root

    def t(xpath):
        return _et_text(inv, xpath, _ET_NS)

    def d(xpath):
        return _et_decimal(inv, xpath, _ET_NS)

    def dt(xpath):
        return _et_date(inv, xpath, _ET_NS)

    lines = []
    for idx, ln in enumerate(inv.xpath("//*[local-name()='InvoiceRow']"), start=1):
        def lt(xp):
            return _et_text(ln, xp, {})

        def ld(xp):
            return _et_decimal(ln, xp, {})

        lines.append(
            {
                "line_number": idx,
                "description": lt("*[local-name()='Description']"),
                "quantity": ld("*[local-name()='ItemQuantity']"),
                "unit": lt("*[local-name()='Unit']"),
                "unit_price": ld("*[local-name()='ItemDetailedPrice']") or ld("*[local-name()='UnitPrice']"),
                "vat_rate": ld("*[local-name()='VAT']/*[local-name()='VATRate']"),
                "net_amount": ld("*[local-name()='RowSum']") or ld("*[local-name()='ItemSum']"),
                "vat_amount": ld("*[local-name()='VAT']/*[local-name()='SumBeforeVAT']"),
                "total_amount": ld("*[local-name()='RowTotal']"),
            }
        )

    return {
        "source": "einvoice_et",
        "invoice_number": t("*[local-name()='InvoiceInformation']/*[local-name()='InvoiceNumber']")
                          or t("*[local-name()='InvoiceNumber']"),
        "invoice_date": dt("*[local-name()='InvoiceInformation']/*[local-name()='InvoiceDate']")
                        or dt("*[local-name()='InvoiceDate']"),
        "due_date": dt("*[local-name()='PaymentInfo']/*[local-name()='DueDate']")
                    or dt("*[local-name()='DueDate']"),
        "supplier_name": t("*[local-name()='SellerParty']/*[local-name()='Name']")
                         or t("*[local-name()='Seller']/*[local-name()='Name']"),
        "supplier_reg_code": t("*[local-name()='SellerParty']/*[local-name()='RegNumber']")
                              or t("*[local-name()='Seller']/*[local-name()='RegNumber']"),
        "supplier_vat_code": t("*[local-name()='SellerParty']/*[local-name()='VATNumber']")
                              or t("*[local-name()='Seller']/*[local-name()='VATNumber']"),
        "customer_name": t("*[local-name()='BuyerParty']/*[local-name()='Name']")
                         or t("*[local-name()='Buyer']/*[local-name()='Name']"),
        "customer_reg_code": t("*[local-name()='BuyerParty']/*[local-name()='RegNumber']")
                              or t("*[local-name()='Buyer']/*[local-name()='RegNumber']"),
        "customer_vat_code": t("*[local-name()='BuyerParty']/*[local-name()='VATNumber']")
                              or t("*[local-name()='Buyer']/*[local-name()='VATNumber']"),
        "currency": t("*[local-name()='InvoiceSumGroup']/*[local-name()='Currency']") or "EUR",
        "net_amount": d("*[local-name()='InvoiceSumGroup']/*[local-name()='InvoiceSum']"),
        "vat_amount": d("*[local-name()='InvoiceSumGroup']/*[local-name()='VAT']/*[local-name()='VATSum']"),
        "total_amount": d("*[local-name()='InvoiceSumGroup']/*[local-name()='TotalSum']"),
        "lines": lines,
    }


# ──────────────────────────────────────────────
# UBL 2.1 parser
# ──────────────────────────────────────────────
_UBL_NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
}


def _ubl_text(element, xpath: str) -> Optional[str]:
    nodes = element.xpath(xpath, namespaces=_UBL_NS)
    if nodes:
        v = nodes[0]
        if hasattr(v, "text"):
            return (v.text or "").strip() or None
        return str(v).strip() or None
    return None


def _ubl_decimal(element, xpath: str) -> Optional[Decimal]:
    val = _ubl_text(element, xpath)
    if val:
        try:
            return Decimal(val)
        except Exception:
            pass
    return None


def _ubl_date(element, xpath: str) -> Optional[date]:
    val = _ubl_text(element, xpath)
    if val:
        try:
            from datetime import datetime
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def parse_ubl_invoice(xml_bytes: bytes) -> dict:
    """Parse a UBL 2.1 Invoice XML into a normalised dict."""
    root = _safe_fromstring(xml_bytes)

    invoice_number = _ubl_text(root, "cbc:ID")
    invoice_date = _ubl_date(root, "cbc:IssueDate")
    due_date = _ubl_date(root, "cac:PaymentMeans/cbc:PaymentDueDate") or _ubl_date(
        root, "cac:PaymentTerms/cbc:Note"
    )
    currency = _ubl_text(root, "cbc:DocumentCurrencyCode") or "EUR"

    supplier_name = _ubl_text(root, "cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name")
    supplier_reg = _ubl_text(
        root, "cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID"
    )
    supplier_vat = _ubl_text(
        root,
        "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
    )

    customer_name = _ubl_text(root, "cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name")
    customer_reg = _ubl_text(
        root, "cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID"
    )
    customer_vat = _ubl_text(
        root,
        "cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
    )

    net_amount = _ubl_decimal(root, "cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount")
    vat_amount = _ubl_decimal(root, "cac:TaxTotal/cbc:TaxAmount")
    total_amount = _ubl_decimal(root, "cac:LegalMonetaryTotal/cbc:PayableAmount")

    lines = []
    for idx, ln in enumerate(root.xpath("cac:InvoiceLine", namespaces=_UBL_NS), start=1):
        lines.append(
            {
                "line_number": idx,
                "description": _ubl_text(ln, "cac:Item/cbc:Description")
                               or _ubl_text(ln, "cac:Item/cbc:Name"),
                "quantity": _ubl_decimal(ln, "cbc:InvoicedQuantity"),
                "unit": _ubl_text(ln, "cbc:InvoicedQuantity/@unitCode"),
                "unit_price": _ubl_decimal(ln, "cac:Price/cbc:PriceAmount"),
                "vat_rate": _ubl_decimal(ln, "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:Percent"),
                "net_amount": _ubl_decimal(ln, "cbc:LineExtensionAmount"),
                "vat_amount": _ubl_decimal(ln, "cac:TaxTotal/cbc:TaxAmount"),
                "total_amount": None,  # UBL doesn't always have line total
            }
        )

    return {
        "source": "ubl",
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "supplier_name": supplier_name,
        "supplier_reg_code": supplier_reg,
        "supplier_vat_code": supplier_vat,
        "customer_name": customer_name,
        "customer_reg_code": customer_reg,
        "customer_vat_code": customer_vat,
        "currency": currency,
        "net_amount": net_amount,
        "vat_amount": vat_amount,
        "total_amount": total_amount,
        "lines": lines,
    }


def parse_einvoice_xml(xml_bytes: bytes) -> dict:
    """Auto-detect and parse e-invoice XML (Estonian 1.2 or UBL 2.1)."""
    root = _safe_fromstring(xml_bytes)
    ns = root.nsmap.get(None, "") or ""
    tag = root.tag

    if "ubl" in ns.lower() or "Invoice-2" in ns or tag.endswith("}Invoice") and "ubl" in ns.lower():
        return parse_ubl_invoice(xml_bytes)

    # Check for UBL root namespace more broadly
    if any("ubl" in (v or "").lower() for v in root.nsmap.values()):
        return parse_ubl_invoice(xml_bytes)

    # Default to Estonian e-invoice format
    return parse_estonian_einvoice(xml_bytes)
