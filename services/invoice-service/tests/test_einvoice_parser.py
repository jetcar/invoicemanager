"""
Tests for Estonian e-invoice 1.2 and UBL 2.1 parsers.
These tests are self-contained and do not require a running database.
"""
from decimal import Decimal
import pytest
from app.services.einvoice_parser import parse_einvoice_xml, parse_estonian_einvoice, parse_ubl_invoice


# ──────────────────────────────────────────────
# Estonian e-invoice 1.2 fixture
# ──────────────────────────────────────────────
_ESTONIAN_EINVOICE_XML_STR = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<EInvoice xmlns="http://www.estfatura.ee/xml/schemas/2019/01/EInvoice">'
    "<Invoice>"
    "<InvoiceInformation>"
    "<InvoiceNumber>INV-2024-001</InvoiceNumber>"
    "<InvoiceDate>2024-01-15</InvoiceDate>"
    "</InvoiceInformation>"
    "<PaymentInfo><DueDate>2024-02-15</DueDate></PaymentInfo>"
    "<SellerParty>"
    "<Name>Test Supplier OU</Name>"
    "<RegNumber>12345678</RegNumber>"
    "<VATNumber>EE123456789</VATNumber>"
    "</SellerParty>"
    "<BuyerParty>"
    "<Name>Test Customer AS</Name>"
    "<RegNumber>87654321</RegNumber>"
    "</BuyerParty>"
    "<InvoiceSumGroup>"
    "<Currency>EUR</Currency>"
    "<InvoiceSum>1000.00</InvoiceSum>"
    "<VAT><VATSum>200.00</VATSum></VAT>"
    "<TotalSum>1200.00</TotalSum>"
    "</InvoiceSumGroup>"
    "<InvoiceRow>"
    "<Description>Software development services</Description>"
    "<ItemQuantity>10</ItemQuantity>"
    "<Unit>h</Unit>"
    "<ItemDetailedPrice>100.00</ItemDetailedPrice>"
    "<VAT><VATRate>20</VATRate><SumBeforeVAT>200.00</SumBeforeVAT></VAT>"
    "<RowSum>1000.00</RowSum>"
    "<RowTotal>1200.00</RowTotal>"
    "</InvoiceRow>"
    "</Invoice>"
    "</EInvoice>"
)
ESTONIAN_EINVOICE_XML = _ESTONIAN_EINVOICE_XML_STR.encode("utf-8")

_UBL_INVOICE_XML_STR = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"'
    ' xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"'
    ' xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">'
    "<cbc:ID>UBL-2024-001</cbc:ID>"
    "<cbc:IssueDate>2024-01-20</cbc:IssueDate>"
    "<cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>"
    "<cac:AccountingSupplierParty><cac:Party>"
    "<cac:PartyName><cbc:Name>UBL Supplier GmbH</cbc:Name></cac:PartyName>"
    "<cac:PartyLegalEntity><cbc:CompanyID>DE123456</cbc:CompanyID></cac:PartyLegalEntity>"
    "</cac:Party></cac:AccountingSupplierParty>"
    "<cac:AccountingCustomerParty><cac:Party>"
    "<cac:PartyName><cbc:Name>UBL Customer SRL</cbc:Name></cac:PartyName>"
    "</cac:Party></cac:AccountingCustomerParty>"
    '<cac:TaxTotal><cbc:TaxAmount currencyID="EUR">200.00</cbc:TaxAmount></cac:TaxTotal>'
    "<cac:LegalMonetaryTotal>"
    '<cbc:TaxExclusiveAmount currencyID="EUR">1000.00</cbc:TaxExclusiveAmount>'
    '<cbc:PayableAmount currencyID="EUR">1200.00</cbc:PayableAmount>'
    "</cac:LegalMonetaryTotal>"
    "<cac:InvoiceLine>"
    "<cbc:ID>1</cbc:ID>"
    '<cbc:InvoicedQuantity unitCode="EA">5</cbc:InvoicedQuantity>'
    '<cbc:LineExtensionAmount currencyID="EUR">1000.00</cbc:LineExtensionAmount>'
    "<cac:Item><cbc:Name>Consulting Services</cbc:Name></cac:Item>"
    "<cac:Price>"
    '<cbc:PriceAmount currencyID="EUR">200.00</cbc:PriceAmount>'
    "</cac:Price>"
    "</cac:InvoiceLine>"
    "</Invoice>"
)
UBL_INVOICE_XML = _UBL_INVOICE_XML_STR.encode("utf-8")


class TestEstonianEInvoiceParser:
    def test_invoice_number(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["invoice_number"] == "INV-2024-001"

    def test_invoice_date(self):
        from datetime import date
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["invoice_date"] == date(2024, 1, 15)

    def test_due_date(self):
        from datetime import date
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["due_date"] == date(2024, 2, 15)

    def test_supplier_name(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["supplier_name"] == "Test Supplier OU"

    def test_supplier_reg_code(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["supplier_reg_code"] == "12345678"

    def test_supplier_vat_code(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["supplier_vat_code"] == "EE123456789"

    def test_customer_name(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["customer_name"] == "Test Customer AS"

    def test_currency(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["currency"] == "EUR"

    def test_net_amount(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["net_amount"] == Decimal("1000.00")

    def test_vat_amount(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["vat_amount"] == Decimal("200.00")

    def test_total_amount(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["total_amount"] == Decimal("1200.00")

    def test_lines_count(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert len(result["lines"]) == 1

    def test_line_description(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["lines"][0]["description"] == "Software development services"

    def test_line_quantity(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["lines"][0]["quantity"] == Decimal("10")

    def test_line_unit_price(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["lines"][0]["unit_price"] == Decimal("100.00")

    def test_source(self):
        result = parse_estonian_einvoice(ESTONIAN_EINVOICE_XML)
        assert result["source"] == "einvoice_et"


class TestUBLParser:
    def test_invoice_number(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["invoice_number"] == "UBL-2024-001"

    def test_invoice_date(self):
        from datetime import date
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["invoice_date"] == date(2024, 1, 20)

    def test_supplier_name(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["supplier_name"] == "UBL Supplier GmbH"

    def test_supplier_reg_code(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["supplier_reg_code"] == "DE123456"

    def test_customer_name(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["customer_name"] == "UBL Customer SRL"

    def test_currency(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["currency"] == "EUR"

    def test_net_amount(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["net_amount"] == Decimal("1000.00")

    def test_vat_amount(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["vat_amount"] == Decimal("200.00")

    def test_total_amount(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["total_amount"] == Decimal("1200.00")

    def test_lines_count(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert len(result["lines"]) == 1

    def test_line_description(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["lines"][0]["description"] == "Consulting Services"

    def test_line_quantity(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["lines"][0]["quantity"] == Decimal("5")

    def test_source(self):
        result = parse_ubl_invoice(UBL_INVOICE_XML)
        assert result["source"] == "ubl"


class TestAutoDetect:
    def test_detects_estonian(self):
        result = parse_einvoice_xml(ESTONIAN_EINVOICE_XML)
        assert result["source"] == "einvoice_et"

    def test_detects_ubl(self):
        result = parse_einvoice_xml(UBL_INVOICE_XML)
        assert result["source"] == "ubl"

    def test_invalid_xml_raises(self):
        with pytest.raises(Exception):
            parse_einvoice_xml(b"not xml")
