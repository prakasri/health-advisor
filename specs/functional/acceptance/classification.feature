# AC-001 — executable with pytest-bdd (backend/tests/bdd). Implements AC-1, AC-2, AC-3.
Feature: HbA1c classification and eligibility
  As an adult who knows my HbA1c
  I want to see which range it falls in
  So that I understand what my result means

  Scenario Outline: Classification boundaries (AC-1)
    Given an eligible adult
    When they submit an HbA1c of <hba1c>
    Then the classification is "<classification>"
    And the label says "<label>"

    Examples:
      | hba1c | classification | label                    |
      | 5.6   | normal         | In the normal range      |
      | 5.65  | prediabetes    | In the prediabetes range |
      | 5.7   | prediabetes    | In the prediabetes range |
      | 6.4   | prediabetes    | In the prediabetes range |
      | 6.45  | diabetes       | In the diabetes range    |
      | 6.5   | diabetes       | In the diabetes range    |

  Scenario Outline: Out-of-range HbA1c is rejected (AC-1)
    When an adult submits an HbA1c of <hba1c>
    Then the API responds with status 422

    Examples:
      | hba1c |
      | 2.9   |
      | 20.1  |

  Scenario Outline: Ineligible users get a referral with no AI call (AC-2)
    Given a user aged <age> who is pregnant "<pregnant>" and has type 1 diabetes "<type1>"
    When they complete an assessment
    Then the report kind is "referral" with reason "<reason>"
    And no LLM call was made

    Examples:
      | age | pregnant | type1 | reason   |
      | 17  | no       | no    | under_18 |
      | 29  | yes      | no    | pregnant |
      | 25  | no       | yes   | type1    |
      | 17  | yes      | no    | under_18 |

  Scenario Outline: Urgent flag (AC-3)
    Given an eligible adult
    When they submit an HbA1c of <hba1c>
    Then urgent is <urgent>

    Examples:
      | hba1c | urgent |
      | 9.9   | false  |
      | 10.0  | true   |
      | 11.2  | true   |

  Scenario: Urgent message leads the report (AC-3)
    Given golden case "G05"
    When the assessment completes
    Then the report status is urgent
    And the rendered report shows the urgent message before the summary
