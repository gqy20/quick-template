"""项目配置的 BDD 验收场景。"""

import json

from pytest_bdd import given, parsers, scenarios, then, when

from scaffold.variables import ProjectVars

scenarios("../features/configuration.feature")


@given("a YAML project configuration", target_fixture="scenario_data")
def yaml_configuration(tmp_path):
    path = tmp_path / "project.yaml"
    path.write_text(
        "project_name: YAML Service\nrepository_username: gqy20\nauthor_name: Example Author\n"
    )
    return {"path": path}


@given(
    parsers.parse('a JSON project configuration with project slug "{slug}"'),
    target_fixture="scenario_data",
)
def json_configuration(tmp_path, slug):
    path = tmp_path / "project.json"
    path.write_text(json.dumps({"project_name": "Ignored Name", "project_slug": slug}))
    return {"path": path}


@given(
    parsers.parse('a project named "{project_name}"'),
    target_fixture="scenario_data",
)
def named_project(project_name):
    return {"extra": {"project_name": project_name}}


@given(
    parsers.parse("a project configuration with line length {line_length:d}"),
    target_fixture="scenario_data",
)
def invalid_line_length(line_length):
    return {"extra": {"line_length": line_length}}


@when("the project variables are built")
def build_project_variables(scenario_data):
    scenario_data["result"] = ProjectVars.build(
        scenario_data.get("path"),
        "python",
        True,
        scenario_data.get("extra"),
    )


@when("the project variables are validated")
def validate_project_variables(scenario_data):
    try:
        ProjectVars.build(None, "python", True, scenario_data["extra"])
    except ValueError as error:
        scenario_data["error"] = error


@then(parsers.parse('the project name is "{expected}"'))
def project_name_matches(scenario_data, expected):
    assert scenario_data["result"].project_name == expected


@then(parsers.parse('the repository username is "{expected}"'))
def repository_username_matches(scenario_data, expected):
    assert scenario_data["result"].repository_username == expected


@then(parsers.parse('the project slug is "{expected}"'))
def project_slug_matches(scenario_data, expected):
    assert scenario_data["result"].project_slug == expected


@then(parsers.parse('the package name is "{expected}"'))
def package_name_matches(scenario_data, expected):
    assert scenario_data["result"].package_name == expected


@then("configuration validation fails")
def configuration_validation_fails(scenario_data):
    assert isinstance(scenario_data.get("error"), ValueError)
