Feature: Email finder
  Given a name and a company domain, mailspot works out the most likely work
  email, verifies candidates, and ranks them. It uses a known pattern when it can
  infer one, and common patterns otherwise.

  Background:
    Given the domain "acme.com" has a mail host "mail.acme.com"

  Scenario: On a non-catch-all domain the first deliverable pattern wins
    Given "mail.acme.com" is not a catch-all server
    And "mail.acme.com" accepts only "jane.doe@acme.com"
    When I find the email for "Jane Doe" at "acme.com"
    Then the best candidate is "jane.doe@acme.com"
    And the method is "permutation"
    And the best candidate has a high confidence

  Scenario: A supplied sample detects the company pattern
    Given "mail.acme.com" is not a catch-all server
    And "mail.acme.com" accepts "j.doe@acme.com"
    And I supply the sample "John Roe" is "j.roe@acme.com"
    When I find the email for "Jane Doe" at "acme.com"
    Then the detected pattern is "{first_initial}.{last}"
    And the best candidate is "j.doe@acme.com"
    And the method is "pattern_detected"

  Scenario: On a catch-all domain the best guess is returned as risky
    Given "mail.acme.com" accepts every address
    When I find the email for "Jane Doe" at "acme.com"
    Then the best candidate is "jane.doe@acme.com"
    And the best candidate is marked risky
    And the result says the domain is accept-all

  Scenario: Accented names are transliterated for the local part
    Given "mail.acme.com" is not a catch-all server
    And "mail.acme.com" accepts only "jose.garcia@acme.com"
    When I find the email for "José García" at "acme.com"
    Then the best candidate is "jose.garcia@acme.com"

  Scenario: A free-provider domain is rejected for finding
    When I find the email for "Jane Doe" at "gmail.com"
    Then the find is rejected because the domain has no company pattern

  Scenario: Every tried candidate is reported
    Given "mail.acme.com" is not a catch-all server
    And "mail.acme.com" accepts only "jane.doe@acme.com"
    When I find the email for "Jane Doe" at "acme.com"
    Then the candidates include "jane.doe@acme.com"
    And each candidate carries its own verification result
