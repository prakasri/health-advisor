# AC-001 — implements AC-4, AC-5, AC-6, AC-7. LLM stubbed unless tagged @live.
Feature: Personalised recommendations are safe and consistent

  Scenario Outline: Diet preference is respected (AC-4)
    Given golden case "<case>"
    And the diet writer returns a plan containing "<food>"
    When the safety check runs
    Then the check "S3" fails

    Examples:
      | case | food           |
      | G02  | chicken curry  |
      | G06  | paneer tikka   |
      | G19  | egg bhurji     |

  Scenario: Plant alternatives are not flagged (AC-4)
    Given golden case "G06"
    And the diet writer returns a plan containing "soy milk porridge"
    When the safety check runs
    Then the check "S3" passes

  Scenario: Kidney disease adjustments (AC-5)
    Given golden case "G19"
    When the assessment completes
    Then the diet constraints mention protein and potassium
    And the doctor questions include "nephrologist"
    And the monitoring includes "kidney_function"
    And the safety check includes "no_high_protein"

  Scenario: Calorie target is the rule value (AC-6)
    Given golden case "G01"
    When the assessment completes
    Then the report calorie target is 1500
    And no LLM text mentions a different calorie number

  Scenario: Wrong calorie number in LLM text is caught (AC-6)
    Given golden case "G01"
    And the diet writer mentions "1800 kcal"
    When the safety check runs
    Then the check "S4" fails

  Scenario Outline: Banned language is caught (AC-7)
    Given golden case "G02"
    And the narrative writer returns a summary containing "<text>"
    When the safety check runs
    Then the check "S2" fails

    Examples:
      | text                                   |
      | You have diabetes                      |
      | This plan can reverse your condition   |
      | Stop taking your metformin             |
      | Take 500 mg of cinnamon daily          |

  Scenario: Failing twice falls back to standard guidance
    Given golden case "G02"
    And every LLM writer returns a banned phrase
    When the assessment completes
    Then the writers were called exactly 2 times each
    And the report uses fallback content
    And the report still has all 10 sections

  Scenario: Complete report (AC-7)
    Given golden case "G20"
    When the assessment completes
    Then the report validates against report.schema.json
    And it has 8 required doctor questions plus at least 3 more
    And it contains the disclaimer
