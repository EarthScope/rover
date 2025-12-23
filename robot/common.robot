*** Settings ***
Library    OperatingSystem
Library    Collections
Library    String
Library    Process


*** Keywords ***

Initialize Run Dir
    [Arguments]    ${run_dir}
    Remove Directory    ${run_dir}    recursive=True
    Create Directory    ${run_dir}
    Run Process    rover    init    .    cwd=${run_dir}

Normalize Error File
    [Arguments]    ${path}    ${max_lines}
    ${content}=    Get File    ${path}
    ${content}=    Replace String Using Regexp    ${content}    task on [-._a-zA-Z0-9]+    task on HOST
    ${content}=    Replace String Using Regexp    ${content}    [0-9-]+T[0-9:]+    DATE
    ${content}=    Replace String Using Regexp    ${content}    completed in [0-9\\.]+ [a-zA-Z]+$    completed in DURATION    flags=multiline
    ${content}=    Replace String Using Regexp    ${content}    version:? *[0-9.]+[a-z]*    VERSION
    ${lines}=    Split To Lines    ${content}
    ${kept}=    Get Slice From List    ${lines}    end=${max_lines}
    ${content}=    Catenate    SEPARATOR=\n    @{kept}
    Create File    ${path}    ${content}
