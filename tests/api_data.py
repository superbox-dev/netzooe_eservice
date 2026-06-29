from __future__ import annotations

from typing import Any

CONSENTS_DATA: list[dict[str, Any]] = [
    {
        "validThrough": {
            "from": "2024-05-04",
            "to": "2024-05-07",
        },
        "serviceProvider": "RC100930",
        "serviceProviderName": "wseg 07614 0523 UW Partenstein",
        "pod": "AT0000000000000000000000011111112",
        "status": "REVOKED",
        "contributionPercentage": "100",
        "energyDirection": "CONSUMPTION",
        "energyCommunityConsent": True,
    },
    {
        "validThrough": {
            "from": "2024-05-04",
            "to": "2025-09-30",
        },
        "serviceProvider": "RC100930",
        "serviceProviderName": "wseg 07614 0523 UW Partenstein",
        "pod": "AT0000000000000000000000011111111",
        "status": "REVOKED",
        "contributionPercentage": "100",
        "energyDirection": "GENERATION",
        "energyCommunityConsent": True,
    },
    {
        "validThrough": {
            "from": "2024-05-29",
            "to": "2024-05-29",
        },
        "serviceProvider": "RC100930",
        "serviceProviderName": "wseg 07614 0523 UW Partenstein",
        "pod": "AT0000000000000000000000011111112",
        "status": "REVOKED",
        "contributionPercentage": "100",
        "energyDirection": "CONSUMPTION",
        "energyCommunityConsent": True,
    },
    {
        "validThrough": {
            "from": "2024-09-10",
            "to": "2025-09-30",
        },
        "serviceProvider": "RC100930",
        "serviceProviderName": "wseg 07614 0523 UW Partenstein",
        "pod": "AT0000000000000000000000011111112",
        "status": "REVOKED",
        "contributionPercentage": "100",
        "energyDirection": "CONSUMPTION",
        "energyCommunityConsent": True,
    },
    {
        "validThrough": {
            "from": "2026-01-26",
            "to": "9999-12-31",
        },
        "serviceProvider": "CC100087",
        "serviceProviderName": "7Energy - Bürgerenergiegemeinschaft für",
        "pod": "AT0000000000000000000000011111112",
        "status": "ACTIVE",
        "contributionPercentage": "95",
        "energyDirection": "CONSUMPTION",
        "energyCommunityConsent": True,
    },
    {
        "validThrough": {
            "from": "2026-01-26",
            "to": "9999-12-31",
        },
        "serviceProvider": "CC100087",
        "serviceProviderName": "7Energy - Bürgerenergiegemeinschaft für",
        "pod": "AT0000000000000000000000011111111",
        "status": "ACTIVE",
        "contributionPercentage": "93",
        "energyDirection": "GENERATION",
        "energyCommunityConsent": True,
    },
    {
        "validThrough": {
            "from": "2026-05-21",
            "to": "9999-12-31",
        },
        "serviceProvider": "RC103550",
        "serviceProviderName": "EEG Oberösterreich RID-11",
        "pod": "AT0000000000000000000000011111111",
        "status": "ACTIVE",
        "contributionPercentage": "7",
        "energyDirection": "GENERATION",
        "energyCommunityConsent": True,
    },
    {
        "validThrough": {
            "from": "2026-05-21",
            "to": "9999-12-31",
        },
        "serviceProvider": "RC103550",
        "serviceProviderName": "EEG Oberösterreich RID-11",
        "pod": "AT0000000000000000000000011111112",
        "status": "ACTIVE",
        "contributionPercentage": "5",
        "energyDirection": "CONSUMPTION",
        "energyCommunityConsent": True,
    },
    {
        "validThrough": {
            "from": "2026-05-21",
            "to": "9999-12-31",
        },
        "serviceProvider": "AT113820",
        "serviceProviderName": "OeMAG Abwicklungsstelle für Ökostrom AG",
        "pod": "AT0000000000000000000000011111111",
        "status": "ACTIVE_UNCHANGEABLE",
        "contributionPercentage": "0",
        "energyCommunityConsent": False,
    },
    {
        "validThrough": {
            "from": "2026-06-17",
            "to": "9999-12-31",
        },
        "serviceProvider": "AT110191",
        "serviceProviderName": "EP Energie Plus GmbH",
        "pod": "AT0000000000000000000000011111112",
        "status": "ACTIVE_UNCHANGEABLE",
        "contributionPercentage": "0",
        "energyCommunityConsent": False,
    },
]


DASHBOARD_DATA: dict[str, Any] = {
    "contractAccounts": [
        {
            "contractAccountNumber": "001",
            "businessPartnerNumber": "100",
        },
        {
            "contractAccountNumber": "002",
            "businessPartnerNumber": "100",
        },
        {
            "contractAccountNumber": "003",
            "businessPartnerNumber": "100",
        },
    ],
}

CONTRACT_ACCOUNT_DATA_1: dict[str, Any] = {
    "contractAccountNumber": "001",
    "businessPartnerNumber": "200",
    "active": True,
    "branch": "STROM",
    "contracts": [
        {
            "branch": "STROM",
            "scaleType": "Gem.Erz. / Erzeugung",
            "active": True,
            "pointOfDelivery": {
                "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
                "meter": {
                    "meterNumber": "3000000",
                },
                "monthlyTrend": {
                    "consumptionOld": {
                        "sum": 701.0,
                        "perDay": 23.36666666666667,
                        "days": 30,
                    },
                    "consumptionNew": {
                        "sum": 776.0,
                        "perDay": 25.86666666666667,
                        "days": 30,
                    },
                    "timerangeOld": {
                        "from": "2026-04-29T00:00:00",
                        "to": "2026-05-28T23:59:59",
                    },
                    "timerangeNew": {
                        "from": "2026-05-29T00:00:00",
                        "to": "2026-06-28T23:59:59",
                    },
                },
                "yearlyTrend": {
                    "consumptionOld": {
                        "sum": 4343.807,
                        "perDay": 11.90084109589041,
                        "days": 365,
                    },
                    "consumptionNew": {
                        "sum": 4492.209,
                        "perDay": 12.30742191780822,
                        "days": 365,
                    },
                    "timerangeOld": {
                        "from": "2024-05-31T00:00:00",
                        "to": "2025-05-30T23:59:59",
                    },
                    "timerangeNew": {
                        "from": "2025-05-31T00:00:00",
                        "to": "2026-05-31T23:59:59",
                    },
                },
                "lastReadings": {
                    "values": [
                        {
                            "meternumber": "3000000",
                            "newResult": {
                                "timestamp": "2026-06-28T00:15:00",
                                "readingValue": 11000.00,
                            },
                        },
                    ],
                },
            },
            "powerGenerationUnit": True,
            "energyCommunityData": {
                "timeslices": [
                    {
                        "energyCommunityId": "AT00300000000RC100930000000965743",
                        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
                        "from": "2024-05-06",
                        "to": "2025-09-30",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2024-05-06",
                                "to": "2025-09-30",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2024-05-06",
                                "to": "2025-09-30",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
                            },
                        ],
                        "profileDataAvailableFrom": "2024-05-06",
                        "profileDataAvailableTo": "2025-09-30",
                    },
                    {
                        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
                        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
                        "from": "2026-01-26",
                        "to": "2026-06-28",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2026-01-26",
                                "to": "2026-06-28",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2026-01-26",
                                "to": "2026-06-28",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
                            },
                        ],
                        "profileDataAvailableFrom": "2026-01-26",
                        "profileDataAvailableTo": "2026-06-28",
                    },
                    {
                        "energyCommunityId": "AT00300000000RC103550000000985681",
                        "energyCommunityName": "EEG Oberösterreich RID-11",
                        "from": "2026-05-21",
                        "to": "2026-06-28",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2026-05-21",
                                "to": "2026-06-28",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2026-05-21",
                                "to": "2026-06-28",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
                            },
                        ],
                        "profileDataAvailableFrom": "2026-05-21",
                        "profileDataAvailableTo": "2026-06-28",
                    },
                ],
                "energyCommunityActive": True,
            },
            "supplier": {
                "id": "AT113820",
                "name": "OeMAG Abwicklungsstelle für Ökostrom AG",
            },
            "synthProfile": "Photovoltaik",
        },
    ],
}

CONTRACT_ACCOUNT_DATA_2: dict[str, Any] = {
    "contractAccountNumber": "002",
    "businessPartnerNumber": "200",
    "active": True,
    "branch": "STROM",
    "contracts": [
        {
            "branch": "STROM",
            "scaleType": "EEG 7ngem",
            "active": True,
            "pointOfDelivery": {
                "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
                "meter": {
                    "meterNumber": "3000000",
                },
                "monthlyTrend": {
                    "consumptionOld": {
                        "sum": 0.0,
                        "perDay": 0.0,
                        "days": 0,
                    },
                    "consumptionNew": {
                        "sum": 0.0,
                        "perDay": 0.0,
                        "days": 0,
                    },
                    "timerangeOld": {
                        "from": "2026-06-28T17:07:11.908037756",
                        "to": "2026-06-29T17:07:11.908038675",
                    },
                    "timerangeNew": {
                        "from": "2026-06-28T17:07:11.908040171",
                        "to": "2026-06-29T17:07:11.908040275",
                    },
                },
                "yearlyTrend": {
                    "consumptionOld": {
                        "sum": 0.0,
                        "perDay": 0.0,
                        "days": 0,
                    },
                    "consumptionNew": {
                        "sum": 0.0,
                        "perDay": 0.0,
                        "days": 0,
                    },
                    "timerangeOld": {
                        "from": "2026-06-28T17:07:11.908041155",
                        "to": "2026-06-29T17:07:11.908041266",
                    },
                    "timerangeNew": {
                        "from": "2026-06-28T17:07:11.908041578",
                        "to": "2026-06-29T17:07:11.908041679",
                    },
                },
                "lastReadings": {
                    "values": [
                        {
                            "meternumber": "3000000",
                            "newResult": {
                                "timestamp": "2026-06-28T00:15:00",
                                "readingValue": 44000.000,
                            },
                        },
                    ],
                },
            },
            "powerGenerationUnit": False,
            "energyCommunityData": {
                "status": "HISTORICAL",
                "timeslices": [
                    {
                        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
                        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
                        "from": "2026-06-17",
                        "to": "2026-06-28",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2026-06-17",
                                "to": "2026-06-28",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2026-06-17",
                                "to": "2026-06-28",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OWN_COVERAGE",
                            },
                        ],
                        "profileDataAvailableFrom": "2026-06-17",
                        "profileDataAvailableTo": "2026-06-28",
                    },
                    {
                        "energyCommunityId": "AT00300000000RC103550000000985681",
                        "energyCommunityName": "EEG Oberösterreich RID-11",
                        "from": "2026-06-17",
                        "to": "2026-06-28",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2026-06-17",
                                "to": "2026-06-28",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2026-06-17",
                                "to": "2026-06-28",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OWN_COVERAGE",
                            },
                        ],
                        "profileDataAvailableFrom": "2026-06-17",
                        "profileDataAvailableTo": "2026-06-28",
                    },
                ],
                "energyCommunityActive": True,
            },
            "supplier": {
                "id": "AT110191",
                "name": "EP Energie Plus GmbH",
            },
            "synthProfile": "Haushalt",
        },
    ],
}

CONTRACT_ACCOUNT_DATA_3: dict[str, Any] = {
    "contractAccountNumber": "003",
    "businessPartnerNumber": "200",
    "active": False,
    "branch": "STROM",
    "contracts": [
        {
            "branch": "STROM",
            "scaleType": "EEG 7ngem",
            "active": False,
            "pointOfDelivery": {
                "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
                "meter": {
                    "meterNumber": "3000000",
                },
                "monthlyTrend": {
                    "consumptionOld": {
                        "sum": 0.0,
                        "perDay": 0.0,
                        "days": 0,
                    },
                    "consumptionNew": {
                        "sum": 0.0,
                        "perDay": 0.0,
                        "days": 0,
                    },
                    "timerangeOld": {
                        "from": "2026-06-28T17:11:06.851202621",
                        "to": "2026-06-29T17:11:06.851203478",
                    },
                    "timerangeNew": {
                        "from": "2026-06-28T17:11:06.85120513",
                        "to": "2026-06-29T17:11:06.851205241",
                    },
                },
                "yearlyTrend": {
                    "consumptionOld": {
                        "sum": 0.0,
                        "perDay": 0.0,
                        "days": 0,
                    },
                    "consumptionNew": {
                        "sum": 0.0,
                        "perDay": 0.0,
                        "days": 0,
                    },
                    "timerangeOld": {
                        "from": "2026-06-28T17:11:06.851206116",
                        "to": "2026-06-29T17:11:06.85120623",
                    },
                    "timerangeNew": {
                        "from": "2026-06-28T17:11:06.851206505",
                        "to": "2026-06-29T17:11:06.85120663",
                    },
                },
                "lastReadings": {},
            },
            "powerGenerationUnit": False,
            "energyCommunityData": {
                "status": "HISTORICAL",
                "timeslices": [
                    {
                        "energyCommunityId": "AT00300000000RC100930000000965743",
                        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
                        "from": "2024-05-06",
                        "to": "2024-05-07",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2024-05-06",
                                "to": "2024-05-07",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2024-05-06",
                                "to": "2024-05-07",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OWN_COVERAGE",
                            },
                        ],
                        "profileDataAvailableFrom": "2024-05-06",
                        "profileDataAvailableTo": "2024-05-07",
                    },
                    {
                        "energyCommunityId": "AT00300000000RC100930000000965743",
                        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
                        "from": "2024-09-10",
                        "to": "2025-09-30",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2024-09-10",
                                "to": "2025-09-30",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2024-09-10",
                                "to": "2025-09-30",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OWN_COVERAGE",
                            },
                        ],
                        "profileDataAvailableFrom": "2024-09-10",
                        "profileDataAvailableTo": "2025-09-30",
                    },
                    {
                        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
                        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
                        "from": "2026-01-26",
                        "to": "2026-06-16",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2026-01-26",
                                "to": "2026-06-16",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2026-01-26",
                                "to": "2026-06-16",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OWN_COVERAGE",
                            },
                        ],
                        "profileDataAvailableFrom": "2026-01-26",
                        "profileDataAvailableTo": "2026-06-16",
                    },
                    {
                        "energyCommunityId": "AT00300000000RC103550000000985681",
                        "energyCommunityName": "EEG Oberösterreich RID-11",
                        "from": "2026-05-21",
                        "to": "2026-06-16",
                        "status": "ACTIVE",
                        "profiles": [
                            {
                                "from": "2026-05-21",
                                "to": "2026-06-16",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
                            },
                            {
                                "from": "2026-05-21",
                                "to": "2026-06-16",
                                "granularity": "QUARTER_OF_AN_HOUR",
                                "profileType": "ENERGY_COMMUNITY_OWN_COVERAGE",
                            },
                        ],
                        "profileDataAvailableFrom": "2026-05-21",
                        "profileDataAvailableTo": "2026-06-16",
                    },
                ],
                "energyCommunityActive": True,
            },
            "supplier": {
                "id": "AT113021",
                "name": "easy green energy GmbH & Co KG",
            },
            "synthProfile": "Haushalt",
        },
    ],
}

PROFILE_DATA_TOTAL_L2_001_1: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2024-10-07T00:00:00",
        "to": "2025-09-30T23:59:59",
        "type": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 8000.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2024-10-07T00:00:00",
        "to": "2025-09-30T23:59:59",
        "type": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 7000.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
]

PROFILE_DATA_TOTAL_L3_001_1: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2024-10-07T00:00:00",
        "to": "2025-09-30T23:59:59",
        "type": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 8000.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2024-10-07T00:00:00",
        "to": "2025-09-30T23:59:59",
        "type": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 7000.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
]

PROFILE_DATA_TOTAL_L2_001_2: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-01-26T00:00:00",
        "to": "2026-06-13T23:59:59",
        "type": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 2000.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-01-26T00:00:00",
        "to": "2026-06-13T23:59:59",
        "type": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 1000.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
]

PROFILE_DATA_MONTHLY_L2_001_2: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-05-01T00:00:00",
        "to": "2026-05-31T23:59:59",
        "type": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 700.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-05-01T00:00:00",
        "to": "2026-05-31T23:59:59",
        "type": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 500.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
]

PROFILE_DATA_TOTAL_L3_001_2: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-01-26T00:00:00",
        "to": "2026-06-27T23:59:59",
        "type": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 2000.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-01-26T00:00:00",
        "to": "2026-06-27T23:59:59",
        "type": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 1400.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
]

PROFILE_DATA_TOTAL_L2_001_3: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-05-21T00:00:00",
        "to": "2026-06-13T23:59:59",
        "type": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 30.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-05-21T00:00:00",
        "to": "2026-06-13T23:59:59",
        "type": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 20.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
]

PROFILE_DATA_MONTHLY_L2_001_3: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-05-21T00:00:00",
        "to": "2026-05-31T23:59:59",
        "type": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 15.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-05-21T00:00:00",
        "to": "2026-05-31T23:59:59",
        "type": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 12.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
]

PROFILE_DATA_TOTAL_L3_001_3: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-05-21T00:00:00",
        "to": "2026-06-27T23:59:59",
        "type": "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 50.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
        "from": "2026-05-21T00:00:00",
        "to": "2026-06-27T23:59:59",
        "type": "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "GENERATION",
        "sum": {
            "value": 40.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
]

PROFILE_DATA_TOTAL_L3_002_1: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-06-17T00:00:00",
        "to": "2026-06-27T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 30.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-06-17T00:00:00",
        "to": "2026-06-27T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 10.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
]

PROFILE_DATA_TOTAL_L3_002_2: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-06-17T00:00:00",
        "to": "2026-06-27T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 2.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-06-17T00:00:00",
        "to": "2026-06-27T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 1.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
]

PROFILE_DATA_TOTAL_L2_003_1: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-05-06T00:00:00",
        "to": "2024-05-07T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 7.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-05-06T00:00:00",
        "to": "2024-05-07T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 2.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
]

PROFILE_DATA_TOTAL_L3_003_1: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-05-06T00:00:00",
        "to": "2024-05-07T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 7.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-05-06T00:00:00",
        "to": "2024-05-07T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 2.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
]

PROFILE_DATA_TOTAL_L2_003_2: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-10-07T00:00:00",
        "to": "2025-09-30T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 4000.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-10-07T00:00:00",
        "to": "2025-09-30T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 350.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
]

PROFILE_DATA_TOTAL_L3_003_2: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-05-06T00:00:00",
        "to": "2024-05-07T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 7.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-10-07T00:00:00",
        "to": "2025-09-30T23:59:59",
        "granularity": "YEAR",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 3800.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-05-06T00:00:00",
        "to": "2024-05-07T23:59:59",
        "granularity": "YEAR",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 2.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2024-10-07T00:00:00",
        "to": "2025-09-30T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 350.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC100930000000965743",
        "energyCommunityName": "wseg 07614 0523 UW Partenstein",
    },
]

PROFILE_DATA_TOTAL_L2_003_3: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-01-26T00:00:00",
        "to": "2026-06-13T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 1500.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-01-26T00:00:00",
        "to": "2026-06-13T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "sum": {
            "value": 600.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
]

PROFILE_DATA_MONTHLY_L2_003_3: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-05-01T00:00:00",
        "to": "2026-05-31T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 100.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-05-01T00:00:00",
        "to": "2026-05-31T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 80.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
]

PROFILE_DATA_TOTAL_L3_003_3: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-01-26T00:00:00",
        "to": "2026-06-16T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 1500.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-01-26T00:00:00",
        "to": "2026-06-16T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 600.000,
            "unit": "KWH",
        },
        "energyCommunityId": "ATCC9999DYNAMCC100087000000000002",
        "energyCommunityName": "7Energy - Bürgerenergiegemeinschaft für erneuerbaren Strom",
    },
]

PROFILE_DATA_TOTAL_L2_003_4: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-05-21T00:00:00",
        "to": "2026-06-13T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 30.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-05-21T00:00:00",
        "to": "2026-06-13T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 2.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
]

PROFILE_DATA_MONTHLY_L2_003_4: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-05-21T00:00:00",
        "to": "2026-05-31T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 15.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-05-21T00:00:00",
        "to": "2026-05-31T23:59:59",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 1.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
]

PROFILE_DATA_TOTAL_L3_003_4: list[dict[str, Any]] = [
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-05-21T00:00:00",
        "to": "2026-06-16T23:59:59",
        "type": "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 28.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
    {
        "meterPointAdministrationNumber": "AT0000000000000000000000011111112",
        "from": "2026-05-21T00:00:00",
        "to": "2026-06-16T23:59:59",
        "granularity": "DAY",
        "type": "ENERGY_COMMUNITY_OWN_COVERAGE",
        "energyDirection": "CONSUMPTION",
        "sum": {
            "value": 3.000,
            "unit": "KWH",
        },
        "energyCommunityId": "AT00300000000RC103550000000985681",
        "energyCommunityName": "EEG Oberösterreich RID-11",
    },
]
