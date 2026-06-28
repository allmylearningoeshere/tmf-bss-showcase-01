"""
Seed data for TMF620 Product Catalog.

Pre-populates the in-memory store with realistic telco product
specifications and offerings so the catalog is never empty when
someone opens Swagger UI.  Called once at import time.
"""

from shared.store import product_specifications, product_offerings

SPEC_BASE = "/productCatalog/v4/productSpecification"
OFFERING_BASE = "/productCatalog/v4/productOffering"
PRICE_BASE = "/productCatalog/v4/productOfferingPrice"


def _seed() -> None:
    if product_specifications or product_offerings:
        return  # already seeded

    # ------------------------------------------------------------------
    # Product Specifications
    # ------------------------------------------------------------------

    specs = [
        {
            "id": "spec-mobile-5g",
            "href": f"{SPEC_BASE}/spec-mobile-5g",
            "name": "5G Mobile Service",
            "description": "Next-generation mobile connectivity with 5G NR support",
            "brand": "TelecoX",
            "productNumber": "SPEC-MOB-5G-001",
            "isBundle": False,
            "lifecycleStatus": "Active",
            "@type": "ProductSpecification",
            "@baseType": "ProductSpecification",
            "productSpecCharacteristic": [
                {
                    "name": "downloadSpeed",
                    "description": "Maximum download speed",
                    "valueType": "string",
                    "productSpecCharacteristicValue": [
                        {"value": "1 Gbps"},
                        {"value": "2 Gbps"},
                    ],
                },
                {
                    "name": "dataAllowance",
                    "description": "Monthly data cap",
                    "valueType": "string",
                    "productSpecCharacteristicValue": [
                        {"value": "50 GB"},
                        {"value": "100 GB"},
                        {"value": "Unlimited"},
                    ],
                },
            ],
        },
        {
            "id": "spec-fibre-ftth",
            "href": f"{SPEC_BASE}/spec-fibre-ftth",
            "name": "FTTH Fibre Broadband",
            "description": "Fibre-to-the-home broadband service",
            "brand": "TelecoX",
            "productNumber": "SPEC-FBB-FTTH-001",
            "isBundle": False,
            "lifecycleStatus": "Active",
            "@type": "ProductSpecification",
            "@baseType": "ProductSpecification",
            "productSpecCharacteristic": [
                {
                    "name": "downloadSpeed",
                    "description": "Maximum download speed",
                    "valueType": "string",
                    "productSpecCharacteristicValue": [
                        {"value": "100 Mbps"},
                        {"value": "500 Mbps"},
                        {"value": "1 Gbps"},
                    ],
                },
                {
                    "name": "technology",
                    "description": "Access technology type",
                    "valueType": "string",
                    "productSpecCharacteristicValue": [
                        {"value": "GPON"},
                        {"value": "XGS-PON"},
                    ],
                },
            ],
        },
        {
            "id": "spec-iptv",
            "href": f"{SPEC_BASE}/spec-iptv",
            "name": "IPTV Entertainment",
            "description": "Internet Protocol Television service with catch-up and on-demand",
            "brand": "TelecoX",
            "productNumber": "SPEC-IPTV-001",
            "isBundle": False,
            "lifecycleStatus": "Active",
            "@type": "ProductSpecification",
            "@baseType": "ProductSpecification",
            "productSpecCharacteristic": [
                {
                    "name": "channelCount",
                    "description": "Number of included channels",
                    "valueType": "integer",
                    "productSpecCharacteristicValue": [
                        {"value": "120"},
                        {"value": "250"},
                    ],
                },
            ],
        },
    ]

    for s in specs:
        product_specifications[s["id"]] = s

    # ------------------------------------------------------------------
    # Product Offering Prices (embedded inline in offerings below)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Product Offerings
    # ------------------------------------------------------------------

    offerings = [
        {
            "id": "offering-5g-unlimited",
            "href": f"{OFFERING_BASE}/offering-5g-unlimited",
            "name": "Mobile 5G Unlimited",
            "description": "Unlimited 5G mobile plan with 2 Gbps speeds",
            "isBundle": False,
            "isSellable": True,
            "lifecycleStatus": "Active",
            "version": "1.0",
            "@type": "ProductOffering",
            "@baseType": "ProductOffering",
            "productSpecification": {
                "id": "spec-mobile-5g",
                "href": f"{SPEC_BASE}/spec-mobile-5g",
                "name": "5G Mobile Service",
                "@referredType": "ProductSpecification",
            },
            "productOfferingPrice": [
                {
                    "id": "price-5g-monthly",
                    "href": f"{PRICE_BASE}/price-5g-monthly",
                    "name": "Monthly recurring charge",
                    "@referredType": "ProductOfferingPrice",
                },
            ],
            "_priceDetail": [
                {
                    "id": "price-5g-monthly",
                    "href": f"{PRICE_BASE}/price-5g-monthly",
                    "name": "Monthly recurring charge",
                    "priceType": "recurring",
                    "recurringChargePeriodType": "monthly",
                    "price": {
                        "taxIncludedAmount": {"unit": "EUR", "value": 49.99},
                        "dutyFreeAmount": {"unit": "EUR", "value": 41.99},
                    },
                    "@type": "ProductOfferingPrice",
                },
            ],
        },
        {
            "id": "offering-fibre-1g",
            "href": f"{OFFERING_BASE}/offering-fibre-1g",
            "name": "Fibre 1 Gbps",
            "description": "Ultra-fast 1 Gbps fibre broadband for home",
            "isBundle": False,
            "isSellable": True,
            "lifecycleStatus": "Active",
            "version": "1.0",
            "@type": "ProductOffering",
            "@baseType": "ProductOffering",
            "productSpecification": {
                "id": "spec-fibre-ftth",
                "href": f"{SPEC_BASE}/spec-fibre-ftth",
                "name": "FTTH Fibre Broadband",
                "@referredType": "ProductSpecification",
            },
            "productOfferingPrice": [
                {
                    "id": "price-fibre-monthly",
                    "href": f"{PRICE_BASE}/price-fibre-monthly",
                    "name": "Monthly recurring charge",
                    "@referredType": "ProductOfferingPrice",
                },
            ],
            "_priceDetail": [
                {
                    "id": "price-fibre-monthly",
                    "href": f"{PRICE_BASE}/price-fibre-monthly",
                    "name": "Monthly recurring charge",
                    "priceType": "recurring",
                    "recurringChargePeriodType": "monthly",
                    "price": {
                        "taxIncludedAmount": {"unit": "EUR", "value": 39.99},
                        "dutyFreeAmount": {"unit": "EUR", "value": 33.60},
                    },
                    "@type": "ProductOfferingPrice",
                },
            ],
        },
        {
            "id": "offering-triple-play",
            "href": f"{OFFERING_BASE}/offering-triple-play",
            "name": "Triple Play Bundle",
            "description": "Fibre broadband + IPTV + 5G mobile in one package",
            "isBundle": True,
            "isSellable": True,
            "lifecycleStatus": "Active",
            "version": "1.0",
            "@type": "ProductOffering",
            "@baseType": "ProductOffering",
            "productSpecification": None,
            "productOfferingPrice": [
                {
                    "id": "price-triple-monthly",
                    "href": f"{PRICE_BASE}/price-triple-monthly",
                    "name": "Bundle monthly charge",
                    "@referredType": "ProductOfferingPrice",
                },
            ],
            "_priceDetail": [
                {
                    "id": "price-triple-monthly",
                    "href": f"{PRICE_BASE}/price-triple-monthly",
                    "name": "Bundle monthly charge",
                    "priceType": "recurring",
                    "recurringChargePeriodType": "monthly",
                    "price": {
                        "taxIncludedAmount": {"unit": "EUR", "value": 79.99},
                        "dutyFreeAmount": {"unit": "EUR", "value": 67.22},
                    },
                    "@type": "ProductOfferingPrice",
                },
            ],
        },
    ]

    for o in offerings:
        product_offerings[o["id"]] = o


# Run on import
_seed()
