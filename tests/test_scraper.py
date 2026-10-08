"""Unit tests for JanSeva openZIM Welfare Scraper & Compiler."""

import pathlib
import pytest
import libzim

from scraper.crawler import WelfareCrawler
from scraper.models import ScraperConfig, WelfareSchemeArticle, SchemeDocumentRequirement
from scraper.offline_dataset import CURATED_WELFARE_SCHEMES
from scraper.parsers import CentralDbtParser, GenericWelfareParser, MySchemeParser
from scraper.welfare_scraper import WelfareZimScraper
from scraper.zim_compiler import openZimCompiler


def test_myscheme_parser_html():
    parser = MySchemeParser()
    sample_html = """
    <html>
      <head><title>PM-KISAN Samman Nidhi | myScheme</title></head>
      <body>
        <h1>Pradhan Mantri Kisan Samman Nidhi</h1>
        <div class="nodal-ministry">Ministry of Agriculture</div>
        <div class="state-badge">All India</div>
        <div class="benefits">Financial assistance of Rs 6,000 per year.</div>
        <div class="eligibility">
          <ul>
            <li>Small and marginal landholder farmer families.</li>
            <li>Must own cultivable land in state records.</li>
          </ul>
        </div>
        <div class="documents">
          <ul>
            <li>Aadhaar Card</li>
            <li>Land RTC 7/12 Extract</li>
          </ul>
        </div>
      </body>
    </html>
    """
    assert parser.can_parse("https://myscheme.gov.in/schemes/pm-kisan", sample_html)
    article = parser.parse("https://myscheme.gov.in/schemes/pm-kisan", sample_html)
    assert article is not None
    assert "Kisan" in article.title
    assert article.state == "All India"
    assert len(article.eligibility_criteria) >= 2
    assert len(article.required_documents) >= 2


def test_myscheme_parser_next_data():
    parser = MySchemeParser()
    sample_html = """
    <html>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
        {
          "props": {
            "pageProps": {
              "schemeData": {
                "basicDetails": {
                  "schemeName": "Atal Pension Yojana",
                  "slug": "atal-pension",
                  "nodalMinistryName": "Ministry of Finance",
                  "state": "All India",
                  "schemeCategory": "Pension"
                },
                "benefits": {
                  "summary": "Guaranteed minimum monthly pension of Rs 1000 to 5000."
                },
                "eligibility": {
                  "criteria": ["Age between 18 and 40 years", "Savings bank account holder"]
                },
                "documents": {
                  "requiredDocuments": [{"documentName": "Aadhaar Card"}, {"documentName": "Bank Passbook"}]
                }
              }
            }
          }
        }
        </script>
      </body>
    </html>
    """
    assert parser.can_parse("https://myscheme.gov.in/schemes/atal-pension", sample_html)
    article = parser.parse("https://myscheme.gov.in/schemes/atal-pension", sample_html)
    assert article is not None
    assert article.title == "Atal Pension Yojana"
    assert article.department == "Ministry of Finance"
    assert len(article.eligibility_criteria) == 2


def test_central_dbt_parser():
    parser = CentralDbtParser()
    sample_html = """
    <html>
      <head><title>Direct Benefit Transfer Bharat</title></head>
      <body>
        <h1>Pradhan Mantri Matru Vandana Yojana</h1>
        <p>Maternity benefit cash incentive directly credited into bank account.</p>
        <ul>
          <li>Pregnant women and lactating mothers aged 19 and above.</li>
          <li>Aadhaar card mandatory for DBT crediting.</li>
          <li>Active bank passbook seeded with NPCI.</li>
        </ul>
      </body>
    </html>
    """
    assert parser.can_parse("https://dbtbharat.gov.in/scheme/pmmvy", sample_html)
    article = parser.parse("https://dbtbharat.gov.in/scheme/pmmvy", sample_html)
    assert article is not None
    assert "Matru" in article.title
    assert any("Aadhaar" in d.name for d in article.required_documents)


def test_generic_welfare_parser():
    parser = GenericWelfareParser()
    sample_html = """
    <html>
      <body>
        <h1>State Crop Relief Scheme</h1>
        <p>Compensation of up to Rs 15,000 per hectare for flood damaged crop.</p>
        <ul>
          <li>Farmer resident of Karnataka state.</li>
          <li>Must present Aadhaar card and crop insurance receipt.</li>
        </ul>
      </body>
    </html>
    """
    assert parser.can_parse("https://example.gov.in/relief", sample_html)
    article = parser.parse("https://example.gov.in/relief", sample_html)
    assert article is not None
    assert "Crop" in article.title
    assert article.state == "Karnataka"


def test_crawler_link_extraction():
    config = ScraperConfig(seed_url="https://welfare.gov.in")
    crawler = WelfareCrawler(config)
    sample_html = """
    <html>
      <body>
        <a href="/schemes/farmer-support">Farmer Support</a>
        <a href="/scheme/scholarship">Scholarship Scheme</a>
        <a href="https://external-ads.com">Ad</a>
        <a href="#section2">Anchor</a>
      </body>
    </html>
    """
    links = crawler._extract_links("https://welfare.gov.in/home", sample_html)
    assert any("farmer-support" in l for l in links)
    assert any("scholarship" in l for l in links)
    assert not any("external-ads.com" in l for l in links)


def test_openzim_compiler(tmp_path: pathlib.Path):
    target_zim = tmp_path / "test_welfare.zim"
    config = ScraperConfig(
        seed_url="https://myscheme.gov.in",
        output_path=target_zim,
        title="Test Kiwix Pack",
        description="Test offline openZIM archive",
        language="eng",
    )

    compiler = openZimCompiler(config)
    # Compile two sample schemes
    articles = CURATED_WELFARE_SCHEMES[:2]
    compiled_path = compiler.compile(articles)

    assert compiled_path.exists()
    assert compiled_path.stat().st_size > 10000

    # Verify openZIM compliance via libzim.Archive
    arch = libzim.Archive(str(compiled_path))
    assert arch.has_main_entry is True
    assert arch.has_fulltext_index is True
    assert arch.has_title_index is True
    assert arch.get_metadata("Title").decode("utf-8") == "Test Kiwix Pack"
    assert arch.get_metadata("Creator").decode("utf-8") == "JanSeva openZIM Scraper Pipeline"

    # Verify entries exist
    entry_index = arch.get_entry_by_path("index.html")
    assert entry_index is not None
    assert "html" in entry_index.get_item().mimetype

    entry_css = arch.get_entry_by_path("assets/offline.css")
    assert entry_css is not None
    assert "css" in entry_css.get_item().mimetype


def test_welfare_scraper_inspect(tmp_path: pathlib.Path):
    target_zim = tmp_path / "inspect_test.zim"
    scraper = WelfareZimScraper()
    zim_file = scraper.generate_curated_welfare_zim(target_zim, title="Inspectable Pack")
    
    info = scraper.inspect_zim(zim_file)
    assert info["filename"] == "inspect_test.zim"
    assert info["article_count"] >= 10
    assert info["has_main_entry"] is True
    assert info["has_fulltext_index"] is True
    assert "Title" in info["metadata"]
