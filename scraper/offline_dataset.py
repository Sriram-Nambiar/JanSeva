"""Curated offline welfare scheme database for openZIM packaging and crawler fallback.

Provides comprehensive, legally grounded data for major Indian Central and State welfare
schemes, ensuring reliable ZIM generation even when government servers are down,
rate-limited, or protected by Cloudflare/geo-blocking.
"""

from typing import List
from scraper.models import SchemeDocumentRequirement, WelfareSchemeArticle

CURATED_WELFARE_SCHEMES: List[WelfareSchemeArticle] = [
    WelfareSchemeArticle(
        id="pm-kisan-samman-nidhi",
        title="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        portal_url="https://pmkisan.gov.in",
        department="Ministry of Agriculture and Farmers Welfare, Govt of India",
        state="All India",
        category="Agriculture & Farmers Welfare",
        benefit_summary="₹6,000 annually paid in three equal 4-monthly installments of ₹2,000 via Direct Benefit Transfer (DBT).",
        eligibility_summary="All landholding farmer families with cultivable landholding in their names as per State Revenue records.",
        eligibility_criteria=[
            "Applicant must be an Indian citizen with cultivable land registered in State Revenue Land Records (Bhoomi / Bhulekh / RoR).",
            "Institutional landholders and serving/retired government officials (Class I, II, III) are excluded.",
            "Professionals like Doctors, Engineers, Lawyers, Chartered Accountants, and Income Tax payees are excluded.",
            "Family definition includes husband, wife, and minor children owning cultivable land.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Aadhaar Card",
                statutory_why="Mandatory citizen authentication under Section 7 of the Aadhaar (Targeted Delivery of Financial Subsidies) Act, 2016.",
            ),
            SchemeDocumentRequirement(
                name="Record of Rights (RTC / 7/12 Extract / Khatauni)",
                statutory_why="Statutory legal proof of operational agricultural land title entered in State Digital Revenue Registry.",
            ),
            SchemeDocumentRequirement(
                name="NPCI-Mapped Bank Passbook",
                statutory_why="Mandatory under DBT Mission Guidelines 2017 to receive APBS credits via the Aadhaar Payment Bridge Switch.",
            ),
        ],
        application_process=[
            "Visit the official PM-KISAN portal (pmkisan.gov.in) or nearest Common Service Centre (CSC).",
            "Click on 'New Farmer Registration' and enter your 12-digit Aadhaar number and registered mobile number.",
            "Select State, District, Sub-District, Block, and Village corresponding to your revenue land records.",
            "Enter survey number, Khata/Khasra number, land area in hectares, and date of land mutation.",
            "Upload self-attested land RTC and bank passbook photocopy. Submit for State Nodal Verification.",
        ],
        common_rejection_pitfalls=[
            "Land mutation pending in state revenue portal after ancestral inheritance (PFMS code PMKISAN_LAND_01).",
            "Name spelling discrepancy between Aadhaar demographic record and Revenue Land Registry.",
            "Bank account is KYC compliant but Aadhaar DBT NPCI seeding mandate was never registered.",
        ],
        nodal_helpline="155261 / 011-24300606 (PM-KISAN Central Helpline)",
        tags=["farmers", "agriculture", "dbt", "cash-transfer", "central-scheme"],
    ),
    WelfareSchemeArticle(
        id="ayushman-bharat-pmjay",
        title="Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)",
        portal_url="https://beneficiary.nha.gov.in",
        department="National Health Authority (NHA), Ministry of Health & Family Welfare",
        state="All India",
        category="Healthcare & Health Insurance",
        benefit_summary="₹5,00,000 cashless secondary and tertiary hospitalisation health coverage per eligible family per year.",
        eligibility_summary="Deprived rural and defined urban occupational households under SECC 2011, NFSA cardholders, and seniors aged 70+.",
        eligibility_criteria=[
            "Rural families categorized under SECC 2011 deprivation criteria (D1 to D7, single-room kuccha houses, disabled heads).",
            "Identified urban workers (ragpickers, domestic helpers, street vendors, transport workers, construction laborers).",
            "All senior citizens aged 70 and above, regardless of family income (Ayushman Vaya Vandana Card).",
            "No restriction on family size, gender, or age of family members.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Aadhaar Card",
                statutory_why="Used for e-KYC biometric/facial authentication and generation of unique 14-digit ABHA (Ayushman Bharat Health Account) ID.",
            ),
            SchemeDocumentRequirement(
                name="Active Ration Card / PM-JAY Family Verification Letter",
                statutory_why="Legal proof establishing linkage between individual patient and beneficiary family unit listed in SECC census.",
            ),
        ],
        application_process=[
            "Visit the NHA Beneficiary Portal (beneficiary.nha.gov.in) or any Empaneled Health Care Provider (EHCP) hospital helpdesk.",
            "Login with mobile number and search eligibility using Aadhaar number or Ration Card number.",
            "Complete facial authentication or Aadhaar OTP e-KYC.",
            "Upon instant verification, download the PVC Ayushman Card or save the digital Ayushman card on mobile.",
        ],
        common_rejection_pitfalls=[
            "Name on Aadhaar differs significantly from census list entry (Error AYUSHMAN_07).",
            "Family member's name was never added to the state digital NFSA ration database.",
        ],
        nodal_helpline="14555 (Toll-Free National Health Authority Helpline)",
        tags=["health", "insurance", "hospital", "cashless", "ayushman"],
    ),
    WelfareSchemeArticle(
        id="pm-awas-yojana-gramin",
        title="Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
        portal_url="https://pmayg.nic.in",
        department="Ministry of Rural Development, Govt of India",
        state="All India",
        category="Housing & Rural Infrastructure",
        benefit_summary="₹1,20,000 in plains and ₹1,30,000 in hilly/difficult/NE states for construction of pucca house + 95 days MGNREGA wages.",
        eligibility_summary="Homeless households and families living in zero/one/two room houses with kutcha wall and roof as per SECC/Awas+.",
        eligibility_criteria=[
            "Family must not own a pucca house anywhere in India.",
            "Must be included in the Permanent Wait List (PWL) based on SECC 2011 or verified Awas+ rural enumeration list.",
            "Must possess land ownership or designated house site patta in the village.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Aadhaar Card",
                statutory_why="Required under DBT guidelines to geotag house construction stages via AwaasSoft inspection app.",
            ),
            SchemeDocumentRequirement(
                name="Bank Passbook (DBT-Enabled)",
                statutory_why="Direct fund transfers are disbursed in 3-4 milestone stages (Plinth, Lintel, Roof, Finish).",
            ),
            SchemeDocumentRequirement(
                name="MGNREGA Job Card",
                statutory_why="Mandatory under Section 6 of PMAY-G guidelines to claim 90-95 days of unskilled construction wages.",
            ),
        ],
        application_process=[
            "Beneficiary selection is finalized during Gram Sabha meetings based on the Awas+ priority score.",
            "Gram Panchayat Secretary or Awas Mitra registers beneficiary KYC on AwaasSoft portal.",
            "Geo-tagged photograph of the vacant site is uploaded.",
            "Sanction order is issued and installment 1 is credited directly to the beneficiary's Aadhaar-linked bank account.",
        ],
        common_rejection_pitfalls=[
            "Disputed land title or absence of clear house site rights in revenue records.",
            "Bank account KYC went dormant between installment releases, causing PFMS escrow bounce.",
        ],
        nodal_helpline="1800-11-6446 (PMAY-G Toll Free Helpline)",
        tags=["housing", "rural", "construction", "mgnrega", "shelter"],
    ),
    WelfareSchemeArticle(
        id="gruha-lakshmi-karnataka",
        title="Gruha Lakshmi Scheme (Karnataka)",
        portal_url="https://sevasindhu.karnataka.gov.in",
        department="Department of Women and Child Development, Govt of Karnataka",
        state="Karnataka",
        category="Women & Family Welfare",
        benefit_summary="₹2,000 monthly financial assistance transferred directly via DBT to the woman head of the family.",
        eligibility_summary="Female head of household indicated on BPL / APL / Antyodaya ration card whose household does not pay IT or GST.",
        eligibility_criteria=[
            "Applicant must be a permanent resident of Karnataka.",
            "Must be listed as the designated Female Head of Family on the Ration Card (Ahara portal).",
            "Neither the woman nor her spouse can be an income tax assessee or registered GST taxpayer.",
            "Only one woman per household card is entitled to receive the monthly transfer.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Karnataka Ration Card (BPL / AAY / APL)",
                statutory_why="Statutory instrument defining household composition and female headship under Karnataka Food Safety Rules.",
            ),
            SchemeDocumentRequirement(
                name="Applicant Aadhaar Card",
                statutory_why="Used for biometric authentication and NPCI bank routing verification.",
            ),
            SchemeDocumentRequirement(
                name="Spouse Aadhaar Card",
                statutory_why="Cross-referenced against Commercial Taxes and Income Tax databases to audit non-taxpayer compliance.",
            ),
        ],
        application_process=[
            "Apply in-person at Grama One, Karnataka One, Bangalore One, or Bapuji Seva Kendra, or online on Seva Sindhu.",
            "Present Ration Card number; portal auto-fetches family details.",
            "Verify Aadhaar OTP or biometric thumbprint.",
            "System prints acknowledgement with unique application reference number.",
        ],
        common_rejection_pitfalls=[
            "Husband or father listed as head of family instead of woman on ration card.",
            "Bank account linked to Aadhaar is inactive or missing NPCI mandate flag.",
        ],
        nodal_helpline="1902 (Seva Sindhu Grievance Helpline)",
        tags=["karnataka", "women", "dbt", "state-scheme", "social-security"],
    ),
    WelfareSchemeArticle(
        id="national-food-security-act-nfsa",
        title="National Food Security Act (NFSA / PMGKAY / Ration)",
        portal_url="https://nfsa.gov.in",
        department="Department of Food and Public Distribution, Govt of India",
        state="All India",
        category="Food & Nutrition Security",
        benefit_summary="5 kg free foodgrains (rice/wheat/coarse grains) per person/month for Priority Households; 35 kg per family for Antyodaya (AAY).",
        eligibility_summary="Households identified as Priority Household (PHH) or Antyodaya Anna Yojana (AAY) under state exclusion limits.",
        eligibility_criteria=[
            "Targeted public distribution system covers up to 75% of rural and 50% of urban population.",
            "Antyodaya Anna Yojana (AAY) covers the poorest of the poor households (destitute, widows, disabled head).",
            "Priority Households (PHH) meeting state-specific income and deprivation thresholds.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Family Aadhaar Cards",
                statutory_why="Mandated by Section 12 of NFSA for biometric e-PoS grain entitlement distribution to eliminate leakages.",
            ),
            SchemeDocumentRequirement(
                name="Income & Residence Certificate",
                statutory_why="Statutory verification by Revenue Authority that household meets BPL income criteria.",
            ),
        ],
        application_process=[
            "Apply through the State Food & Civil Supplies portal or CSC / Fair Price Shop.",
            "Submit family member demographic details with Aadhaar seeding consent.",
            "Local Food Inspector conducts field inquiry on household deprivation criteria.",
            "Digital Ration card is issued with assigned Fair Price Shop (FPS) dealer code.",
        ],
        common_rejection_pitfalls=[
            "Periodic biometric e-KYC not completed at Fair Price Shop e-PoS device (Code NFSA_RC_09).",
            "Household exceeds urban exclusion criteria (e.g., four-wheeler ownership or high power usage).",
        ],
        nodal_helpline="1967 / 1800-180-2087 (National Food Toll Free Helpline)",
        tags=["food", "ration", "nfsa", "grain", "subsidy"],
    ),
    WelfareSchemeArticle(
        id="pm-mudra-yojana",
        title="Pradhan Mantri MUDRA Yojana (PMMY)",
        portal_url="https://mudra.org.in",
        department="Department of Financial Services, Ministry of Finance, Govt of India",
        state="All India",
        category="Banking, Financial Services & Insurance",
        benefit_summary="Collateral-free micro loans up to ₹10 Lakhs (Shishu: up to ₹50K, Kishore: ₹50K-₹5 Lakhs, Tarun: ₹5-10 Lakhs, Tarun Plus: ₹20 Lakhs).",
        eligibility_summary="Non-Corporate, Non-Farm Small/Micro enterprises engaged in manufacturing, trading, and services.",
        eligibility_criteria=[
            "Any Indian citizen who has a business plan for a non-farm sector income generating activity.",
            "Applicant should not be a defaulter to any bank or financial institution.",
            "Satisfactory credit track record.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Identity & Address Proof (Aadhaar / Voter ID / PAN)",
                statutory_why="Mandatory KYC compliance under Reserve Bank of India Master Directions on KYC.",
            ),
            SchemeDocumentRequirement(
                name="Business Enterprise Registration / Udyam Certificate",
                statutory_why="Statutory registration under MSME Development Act verifying micro-enterprise status.",
            ),
            SchemeDocumentRequirement(
                name="Bank Statement (Past 6 Months)",
                statutory_why="Financial institution debt-servicing ability evaluation under Credit Guarantee Scheme for Micro Units (CGFMU).",
            ),
        ],
        application_process=[
            "Apply online through Udyamimitra portal (udyamimitra.in) or visit any Commercial Bank / RRB / MFI.",
            "Select loan category (Shishu / Kishore / Tarun) based on business requirement.",
            "Submit project report, quotation for machinery/equipment, and enterprise registration.",
            "Bank verifies and sanctions loan without seeking collateral or third-party guarantor.",
        ],
        common_rejection_pitfalls=[
            "CIBIL/credit score impairment or prior un-regularized credit card / loan default.",
            "Absence of Udyam MSME registration for Kishore/Tarun stage applications.",
        ],
        nodal_helpline="1800-180-1111 (MUDRA National Toll Free)",
        tags=["msme", "loan", "business", "mudra", "entrepreneurship"],
    ),
    WelfareSchemeArticle(
        id="pm-svanidhi-street-vendor",
        title="PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        portal_url="https://pmsvanidhi.mohua.gov.in",
        department="Ministry of Housing and Urban Affairs (MoHUA), Govt of India",
        state="All India",
        category="Urban Livelihoods & Street Vendors",
        benefit_summary="Working capital collateral-free credit: 1st tranche ₹10,000, 2nd tranche ₹20,000, 3rd tranche ₹50,000 with 7% interest subsidy & cashback on digital transactions.",
        eligibility_summary="All street vendors engaged in vending in urban areas on or before March 24, 2020.",
        eligibility_criteria=[
            "Vendors in possession of Certificate of Vending / Identity Card issued by Urban Local Bodies (ULBs).",
            "Vendors identified in the survey but who have not been issued Certificate of Vending.",
            "Vendors who have been left out of the ULB-led identification survey or started vending after completion of survey and possess Letter of Recommendation (LoR).",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Aadhaar Card",
                statutory_why="Required for e-KYC and digital subsidy distribution via DBT under Section 7 of Aadhaar Act.",
            ),
            SchemeDocumentRequirement(
                name="Certificate of Vending / Identity Card / ULB LoR",
                statutory_why="Statutory recognition under Street Vendors (Protection of Livelihood and Regulation of Street Vending) Act, 2014.",
            ),
            SchemeDocumentRequirement(
                name="Bank Account Details & UPI QR Code",
                statutory_why="Mandatory to claim monthly digital cashback incentives (up to ₹100/month).",
            ),
        ],
        application_process=[
            "Access PM SVANidhi Portal or mobile app directly or through a Common Service Centre (CSC).",
            "Verify Aadhaar OTP and enter Certificate of Vending / LoR number.",
            "Choose preferred lending institution (Public Sector Bank, Private Bank, RRB, SHG).",
            "Loan is sanctioned and disbursed directly into beneficiary account within 7 to 10 days.",
        ],
        common_rejection_pitfalls=[
            "Vending location outside designated urban local body jurisdiction.",
            "Delay in repaying 1st tranche prevents sanction of 2nd higher tranche.",
        ],
        nodal_helpline="1800-11-1979 (PM SVANidhi Toll Free)",
        tags=["street-vendors", "micro-credit", "urban", "subsidy", "svanidhi"],
    ),
    WelfareSchemeArticle(
        id="atal-pension-yojana",
        title="Atal Pension Yojana (APY)",
        portal_url="https://npscra.nsdl.co.in",
        department="Pension Fund Regulatory and Development Authority (PFRDA), Ministry of Finance",
        state="All India",
        category="Social Security & Pensions",
        benefit_summary="Guaranteed minimum monthly pension of ₹1,000, ₹2,000, ₹3,000, ₹4,000 or ₹5,000 from age 60 until death, followed by lifetime pension to spouse and corpus return to nominee.",
        eligibility_summary="All Indian citizens aged between 18 and 40 years holding a savings bank account. Income tax payees excluded.",
        eligibility_criteria=[
            "Age between 18 and 40 years at the time of enrollment.",
            "Must have an active savings bank account with auto-debit enabled.",
            "Should not be an income-tax payer (w.e.f. October 1, 2022).",
            "Minimum 20 years of continuous monthly/quarterly contribution required.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Aadhaar Card",
                statutory_why="Identity authentication and nominee record seeding under PFRDA (Atal Pension Yojana) Regulations.",
            ),
            SchemeDocumentRequirement(
                name="Savings Bank Account Passbook",
                statutory_why="Mandatory for executing recurring automated debit mandates on scheduled installment dates.",
            ),
        ],
        application_process=[
            "Approach the bank branch or post office where your savings account is held.",
            "Fill the APY Registration Form detailing nominee and spouse particulars.",
            "Select the pension slab (e.g. ₹5,000/month) and debit frequency (monthly, quarterly, half-yearly).",
            "A Permanent Retirement Account Number (PRAN) is issued and auto-debit begins.",
        ],
        common_rejection_pitfalls=[
            "Insufficient bank account balance on auto-debit date causing account deactivation.",
            "Applicant enrolled after becoming an income tax payer, resulting in mandatory cancellation.",
        ],
        nodal_helpline="1800-110-069 (PFRDA Toll Free Helpline)",
        tags=["pension", "retirement", "social-security", "apy", "savings"],
    ),
    WelfareSchemeArticle(
        id="sukanya-samriddhi-yojana",
        title="Sukanya Samriddhi Yojana (SSY)",
        portal_url="https://www.indiapost.gov.in",
        department="Ministry of Finance / Department of Posts, Govt of India",
        state="All India",
        category="Women & Child Development",
        benefit_summary="High sovereign-backed interest rate (8.2% p.a.), tax-free returns under Section 80C, and lump sum maturity for girl child's higher education and marriage.",
        eligibility_summary="Girl child who is an Indian resident from birth up to age 10. Maximum 2 accounts per family (except twins/triplets).",
        eligibility_criteria=[
            "Account can be opened by the natural or legal guardian in the name of a girl child.",
            "Girl child age must be below 10 years on date of account opening.",
            "Minimum deposit of ₹250 per financial year; maximum ₹1,50,000.",
            "Maturity is 21 years from date of opening or upon marriage after age 18.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Birth Certificate of Girl Child",
                statutory_why="Statutory legal proof of date of birth and parentage under Registration of Births and Deaths Act.",
            ),
            SchemeDocumentRequirement(
                name="Guardian Aadhaar & PAN Card",
                statutory_why="Mandatory KYC verification under Prevention of Money Laundering (Maintenance of Records) Rules.",
            ),
        ],
        application_process=[
            "Visit any Post Office branch or authorized public/private commercial bank.",
            "Submit the Sukanya Samriddhi Account Opening Form along with girl child birth certificate.",
            "Deposit the initial account opening sum (minimum ₹250).",
            "Post Office / Bank issues the SSY physical passbook with account number.",
        ],
        common_rejection_pitfalls=[
            "Girl child reached age > 10 years before account opening date.",
            "Third account attempted for a family without medical twin/triplet certificate.",
        ],
        nodal_helpline="1800-266-6868 (India Post National Helpline)",
        tags=["girl-child", "savings", "education", "tax-benefit", "sukanya"],
    ),
    WelfareSchemeArticle(
        id="pm-vishwakarma-scheme",
        title="PM Vishwakarma Scheme",
        portal_url="https://pmvishwakarma.gov.in",
        department="Ministry of Micro, Small and Medium Enterprises (MoMSME), Govt of India",
        state="All India",
        category="Artisans, Craftsmen & Livelihood",
        benefit_summary="Recognition through PM Vishwakarma Certificate & ID, skill training with ₹500/day stipend, ₹15,000 toolkit grant, and collateral-free enterprise loans up to ₹3 Lakhs at 5% interest.",
        eligibility_summary="Traditional artisans and craftspeople working with hands and tools in 18 notified family-based trades.",
        eligibility_criteria=[
            "Artisan working in 18 recognized traditional trades (Carpenter, Blacksmith, Goldsmith, Potter, Sculptor, Cobbler, Mason, Weaver, Barber, Tailor, etc.).",
            "Minimum age of 18 years on the date of application.",
            "Beneficiary should be engaged in the trade and should not have availed credit under PMEGP or MUDRA in the past 5 years.",
            "Only one member per family is eligible to enroll.",
        ],
        required_documents=[
            SchemeDocumentRequirement(
                name="Aadhaar Card",
                statutory_why="Mandatory biometric e-KYC authentication and DBT benefit linkage.",
            ),
            SchemeDocumentRequirement(
                name="Active Bank Passbook",
                statutory_why="Required for crediting daily skill training stipend (₹500/day) and modern toolkit grant (₹15,000).",
            ),
            SchemeDocumentRequirement(
                name="Ration Card / Family Proof",
                statutory_why="Mandatory check enforcing the rule of one beneficiary per family unit.",
            ),
        ],
        application_process=[
            "Enroll at the nearest Common Service Centre (CSC) with biometric authentication.",
            "Select trade from the 18 eligible artisan categories.",
            "Three-tier verification: Gram Panchayat / Urban Local Body verification, followed by District Implementation Committee, and National Screening.",
            "Undergo 5-7 days basic skill verification training, receive toolkit grant and digital Vishwakarma card.",
        ],
        common_rejection_pitfalls=[
            "Gram Panchayat / Ward Councilor trade verification rejected due to lack of traditional work proof.",
            "Another family member already enrolled in the scheme.",
        ],
        nodal_helpline="1800-267-7777 / 011-23061500 (PM Vishwakarma Helpline)",
        tags=["artisans", "craftsmen", "vishwakarma", "toolkits", "skill-training"],
    ),
]
