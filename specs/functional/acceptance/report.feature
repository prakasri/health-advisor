# AC-001 — implements AC-8, AC-9.
Feature: Report download and sharing

  Background:
    Given a completed assessment for golden case "G02"

  Scenario: PDF download (AC-8)
    When I request the PDF
    Then the response is a PDF within 5 seconds
    And the PDF text contains "Questions to Discuss with a Doctor"
    And the PDF text contains the disclaimer

  Scenario: Share link opens without login (AC-8)
    When I create a share link
    Then the link expires 30 days from now
    And opening the link returns the report

  Scenario: Revoked link (AC-8)
    Given I created a share link
    When I revoke it
    Then opening the link returns 404

  Scenario: Expired link (AC-8)
    Given a share link that expired yesterday
    When I open it
    Then the response is 404

  @live
  Scenario: Latency (AC-9)
    When 10 assessments run end to end against the live LLM
    Then the 95th percentile duration is under 30 seconds
