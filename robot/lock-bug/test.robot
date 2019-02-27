
*** Settings ***

Library    Process
Library    OperatingSystem


*** Comment ***

To trigger this reliably we need multiple entries in the lock table:
  we download a bunch of sites so that there is idnexing work to be done
  we force indexing with --all in the config 
  mseedindex-cmd has a "sleep" so that it runs slowly
  a side-effect of the above is warnings about the leap seconds file
  in the logs.  we don't care, but they appear at random places, so
  we delete them from the logs before comparison


*** Test Cases ***

Lock File Bug

    Remove Directory    ${CURDIR}${/}run  recursive=True
    Create Directory    ${CURDIR}${/}run
    Remove Directory    ${CURDIR}${/}logs  recursive=True


    Run Process    rover  -f  ../rover.config  retrieve  I?_T*_00_BH1  2018-01-01T00:00:00  2018-01-01T01:00:00  cwd=${CURDIR}${/}run  stderr=retrieve-log-1.txt
    
    Run Process    sed  -i.bak  -E  -e  s/task on [-._a-zA-Z0-9]+/task on HOST/g  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/[0-9-]+T[0-9:]+/DATE/g  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/completed in [0-9\.]+ [a-zA-Z]+$/completed in DURATION/g  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  /.*Warning: No leap.*/d  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  /.*highly recommended.*/d  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/version:? *[0-9.]+[a-z]*/VERSION/g  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-log-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-log-1.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  list-index  net\=*  join-qsr  cwd=${CURDIR}${/}run  stdout=list-index-1.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index-1.txt
    Should Be Equal    ${run}  ${target}


    Run Process    rover  -f  ../rover.config  retrieve  IU_T*_00_BH1  2018-01-01T00:00:00  2018-01-01T01:00:00  cwd=${CURDIR}${/}run  stderr=retrieve-log-2.txt
    
    Run Process    sed  -i.bak  -E  -e  s/task on [-._a-zA-Z0-9]+/task on HOST/g  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/[0-9-]+T[0-9:]+/DATE/g  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/completed in [0-9\.]+ [a-zA-Z]+$/completed in DURATION/g  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  /.*Warning: No leap.*/d  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  /.*highly recommended.*/d  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/version:? *[0-9.]+[a-z]*/VERSION/g  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-log-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-log-2.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  list-index  net\=*  join-qsr  cwd=${CURDIR}${/}run  stdout=list-index-2.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index-2.txt
    Should Be Equal    ${run}  ${target}

