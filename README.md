# AD LDAP

Publisher: Splunk <br>
Connector Version: 2.3.9 <br>
Product Vendor: Splunk <br>
Product Name: Active Directory LDAP <br>
Minimum Product Version: 7.0.0

App specifically designed for interacting with Microsoft Active Directory's LDAP Implementation

## App Information

- This LDAP application utilizes the LDAP3 library for Python. This was chosen, in part, due to
  the pythonic design of the library and the quality of the documentation. Both SSL and TLS are
  supported.
- Please make sure to view additional documentation for this app on our [GitHub Open Source
  Repo!](https://github.com/phantomcyber/phantom-apps/tree/next/Apps/phadldap#readme)

## LDAP Ports Requirements (Based on Standard Guidelines of [IANA ORG](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml) )

- LDAP(service) TCP(transport protocol) - 389
- LDAP(service) UDP(transport protocol) - 389
- LDAP(service) TCP(transport protocol) over TLS/SSL (was sldap) - 636
- LDAP(service) UDP(transport protocol) over TLS/SSL (was sldap) - 636

## Asset Configuration

The asset for this app requires an account with which to Bind and perform actions. If you are only
ever going to perform information gathering tasks (e.g. getting account attributes) then a standard
user account would be fine. However, if you plan on doing things like Unlocking, Resetting
Passwords, Moving objects, etc. - then you will need an account with permissions to actually perform
these actions. It is best practice to NOT use a "Domain Administrator" (or higher) account. Instead,
delegate the appropriate least-privilege access to a service account with a very strong password.
Lastly, it is strongly recommended to use SSL and disallow insecure (plain text and unsigned binds)
if at all possible.

## To add a custom certificate to the certificate store, follow the below steps:

- Need to install the certificate on the server

  - Upload the SSL certificate on the server
  - Go to /opt/phantom/bin and execute the import_cert.py script using command:\
    **phenv python3 import_cert.py -i "path_of_certificate_on_server"**

- Go to etc/hosts using the root user. Assign the domain to IP to use the SSL certificate

**Note:** For reference: [Splunk
Docs](https://docs.splunk.com/Documentation/SOARonprem/latest/Admin/AddOrRemoveCertificates)

## Run Query Action

This action provides the user the ability to run generic queries with the LDAP syntax. The action
takes a filter (in LDAP syntax), an optional search base to search within, and specific attributes
that you would like to return.

- Common AD LDAP Run Query Examples

  - Get Users belonging to a specific OU, Container, or Group

    - filter = (samaccountname=\*)
    - attributes = samaccountname;mail
    - search_base = distinguishedNameOfOU/Container/Group

  - List Group Names that a User belongs to

    - filter = (&(member=distinguishedNameOfUserHERE)(objectClass=group))
    - attributes = name

  - Return results if mail attribute is present OR sAMAccountName matches '\*admin\*'

    - filter = (|(mail=\*)(samaccountname=\*admin\*))
    - attributes = samaccountname;mail;userprincipalname;distinguishedname

  - If you would like to learn more about LDAP Filter Syntax, check out this [Microsoft
    Wiki](https://social.technet.microsoft.com/wiki/contents/articles/5392.active-directory-ldap-syntax-filters.aspx)

### Configuration variables

This table lists the configuration variables required to operate AD LDAP. These variables are specified when configuring a Active Directory LDAP asset in Splunk SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**server** | required | string | The Active Directory Server hostname, IP, or VIP for binding |
**username** | required | string | The username with which to bind to LDAP |
**password** | required | password | The password for the binding user |
**force_ssl** | optional | boolean | Force the use of SSL protocol. Note that some actions are not possible without secure binding! |
**validate_ssl_cert** | optional | boolean | Select if you want to validate the LDAP SSL certificate |
**ssl_port** | required | numeric | The port to bind for SSL (default 636) |

### Supported Actions

[test connectivity](#action-test-connectivity) - test connectivity <br>
[run query](#action-run-query) - Query Active Directory LDAP <br>
[get attributes](#action-get-attributes) - Get attributes of various principals

## action: 'test connectivity'

test connectivity

Type: **test** <br>
Read only: **True**

Basic test for app.

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'run query'

Query Active Directory LDAP

Type: **investigate** <br>
Read only: **True**

This action flexibly supports querying Active Directory using LDAP syntax.

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**filter** | required | The LDAP filter (must be in LDAP Syntax) | string | |
**search_base** | optional | The search base to use in its distinguishedName format. If not specified, the 'defaultNamingContext' will be used | string | |
**attributes** | required | Semi-colon separated list of attributes to collect (e.g. sAMAccountName;mail) | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.filter | string | | |
action_result.parameter.search_base | string | | |
action_result.parameter.attributes | string | | |
action_result.data.\*.entries.\*.dn | string | | CN=SVC-TEST,OU=TEST,DC=TEST,DC=LAB |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'get attributes'

Get attributes of various principals

Type: **investigate** <br>
Read only: **True**

This action takes any number of principals (sAMAccountName, distinguishedName, or userprincipalname) and returns requested attributes. Separate with semi-colon (';').

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**principals** | required | The semi-colon separated principals. These can be sAMAccountName, userprincipalname, or distinguishedName | string | |
**attributes** | required | Semi-colon separated list of attributes to collect | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.principals | string | | |
action_result.parameter.attributes | string | | |
action_result.data.\*.entries.\*.dn | string | | CN=SVC-TEST,OU=TEST,DC=TEST,DC=LAB |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2026 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
