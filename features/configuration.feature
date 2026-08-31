Feature: Project configuration
  The generator accepts reproducible configuration files and rejects invalid
  project metadata before writing files.

  Scenario: Load project metadata from YAML
    Given a YAML project configuration
    When the project variables are built
    Then the project name is "YAML Service"
    And the repository username is "gqy20"

  Scenario: Preserve an explicit project slug
    Given a JSON project configuration with project slug "custom-service"
    When the project variables are built
    Then the project slug is "custom-service"
    And the package name is "custom_service"

  Scenario: Normalize a project name into stable identifiers
    Given a project named "Café Data API!"
    When the project variables are built
    Then the project slug is "cafe-data-api"
    And the package name is "cafe_data_api"

  Scenario: Reject an invalid line length
    Given a project configuration with line length 40
    When the project variables are validated
    Then configuration validation fails
