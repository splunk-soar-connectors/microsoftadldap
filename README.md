# AD LDAP

Publisher: Splunk \
Connector Version: 2.3.4 \
Product Vendor: Splunk \
Product Name: Active Directory LDAP \
Minimum Product Version: 6.3.0

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

[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration \
[add group members](#action-add-group-members) - Adds one or more Active Directory objects to one or more groups \
[remove group members](#action-remove-group-members) - Removes one or more Active Directory objects from one or more groups \
[unlock account](#action-unlock-account) - Unlocks a locked Active Directory account \
[disable account](#action-disable-account) - Disables an Active Directory account \
[enable account](#action-enable-account) - Enables a disabled Active Directory account \
[reset password](#action-reset-password) - Resets the password of a user, requiring the user to change password at next login \
[set password](#action-set-password) - Set a user's password \
[move object](#action-move-object) - Moves an entry in Active Directory \
[run query](#action-run-query) - Query Active Directory LDAP \
[get attributes](#action-get-attributes) - Get attributes of various principals \
[set attribute](#action-set-attribute) - Add, delete, or replace an attribute of a user \
[rename object](#action-rename-object) - Rename the object

## action: 'test connectivity'

Validate the asset configuration for connectivity using supplied configuration

Type: **test** \
Read only: **True**

#### Action Parameters

No parameters are required for this action

#### Action Output

No Output

## action: 'add group members'

Adds one or more Active Directory objects to one or more groups

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use_samaccountname** | optional | Specify members AND groups as sAMAccountName(s) instead of distinguishedName(s) (note: member AND groups will use sAMAccountName if selected) | boolean | |
**members** | required | Semi-colon (';') separated list of users. If 'use samaccountname' is false, then these must be distinguishedName(s) | string | |
**groups** | required | Semi-colon (';') separated list of groups to which the members will be added. If 'use samaccountname' is false, then these must be distinguishedName(s) | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.groups | string | | Domain Guests |
action_result.parameter.members | string | | svc-test |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.data.\*.function | string | | added |
action_result.data.\*.group | string | | cn=domain guests,cn=users,dc=test,dc=lab |
action_result.data.\*.member | string | | cn=svc-test,ou=test,dc=test,dc=lab |
action_result.summary | string | | |
action_result.summary.found_user_records | numeric | | 1 |
action_result.summary.requested_user_records | numeric | | 1 |
action_result.message | string | | added member(s) to group(s) |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'remove group members'

Removes one or more Active Directory objects from one or more groups

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use_samaccountname** | optional | Specify members AND groups as sAMAccountName(s) instead of distinguishedName(s) | boolean | |
**members** | required | Semi-colon (';') separated list of users. If 'use samaccountname' is false, then these must be distinguishedName(s) | string | |
**groups** | required | Semi-colon (';') separated list of groups from which the members will be removed. If 'use samaccountname' is false, then these must be distinguishedName(s) | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.groups | string | | Domain Guests |
action_result.parameter.members | string | | svc-test |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.data.\*.function | string | | removed |
action_result.data.\*.group | string | | cn=domain guests,cn=users,dc=test,dc=lab |
action_result.data.\*.member | string | | cn=svc-test,ou=test,dc=test,dc=lab |
action_result.summary | string | | |
action_result.summary.found_user_records | numeric | | 1 |
action_result.summary.requested_user_records | numeric | | 1 |
action_result.message | string | | removed member(s) from group(s) |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'unlock account'

Unlocks a locked Active Directory account

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use_samaccountname** | optional | Use sAMAccountName for user instead of distinguishedName(s) | boolean | |
**user** | required | Specify the user to unlock. If 'use samaccountname' is false, then this must be the user's distinguishedName | string | `user name` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.parameter.user | string | `user name` | CN=DEFAULTACCOUNT,CN=USERS,DC=TEST,DC=LAB |
action_result.data.\*.samaccountname | string | | |
action_result.data.\*.unlocked | boolean | | True |
action_result.data.\*.user_dn | string | | cn=defaultaccount,cn=users,dc=test,dc=lab |
action_result.summary | string | | |
action_result.summary.unlocked | numeric | | True |
action_result.message | string | | Unlocked: True |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'disable account'

Disables an Active Directory account

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use_samaccountname** | optional | Specify sAMAccountName instead of distinguishedName | boolean | |
**user** | required | Specify the user to disable. If 'use samaccountname' is false, then this must be the user's distinguishedName | string | `user name` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.parameter.user | string | `user name` | CN=DEFAULTACCOUNT,CN=USERS,DC=TEST,DC=LAB |
action_result.data.\*.starting_status | string | | enabled |
action_result.data.\*.user_dn | string | | cn=defaultaccount,cn=users,dc=test,dc=lab |
action_result.summary.account_status | string | | disabled |
action_result.message | string | | Account status: disabled |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'enable account'

Enables a disabled Active Directory account

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use_samaccountname** | optional | Specify sAMAccountName instead of distinguishedName | boolean | |
**user** | required | Specify the user to enable. If 'use samaccountname' is false, then this must be the user's distinguishedName | string | `user name` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.parameter.user | string | `user name` | CN=DEFAULTACCOUNT,CN=USERS,DC=TEST,DC=LAB |
action_result.data.\*.starting_status | string | | disabled |
action_result.data.\*.user_dn | string | | cn=defaultaccount,cn=users,dc=test,dc=lab |
action_result.summary.account_status | string | | enabled |
action_result.message | string | | Account status: enabled |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'reset password'

Resets the password of a user, requiring the user to change password at next login

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use_samaccountname** | optional | Use sAMAccountName instead of distinguishedName | boolean | |
**user** | required | User whose attributes are to be modified | string | `user name` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.parameter.user | string | `user name` | SVC-TEST |
action_result.data.\*.reset | numeric | | True |
action_result.data.\*.samaccountname | string | | SVC-TEST |
action_result.data.\*.user_dn | string | | CN=SVC-TEST,OU=TEST,DC=TEST,DC=LAB |
action_result.summary.reset | numeric | | True |
action_result.message | string | | Reset: True |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'set password'

Set a user's password

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use_samaccountname** | optional | Specify sAMAccountName instead of distinguishedName | boolean | |
**user** | required | Specify the user whose password will be set. If 'use samaccountname' is false, then this must be the user's distinguishedName | string | `user name` |
**password** | required | New password | string | |
**confirm_password** | required | Re-type the password | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.confirm_password | string | | Thisisanewpw!123 |
action_result.parameter.password | string | | Thisisanewpw!123 |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.parameter.user | string | `user name` | CN=DEFAULTACCOUNT,CN=USERS,DC=TEST,DC=LAB |
action_result.data.\*.samaccountname | string | | |
action_result.data.\*.set | boolean | | True |
action_result.data.\*.user_dn | string | | cn=defaultaccount,cn=users,dc=test,dc=lab |
action_result.summary | string | | |
action_result.summary.set | numeric | | True |
action_result.message | string | | Set: True |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'move object'

Moves an entry in Active Directory

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**object** | required | Specify the distinguishedName to move | string | |
**destination_ou** | required | The distinguishedName of the OU the specified object will move to | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.destination_ou | string | | OU=TEST,DC=TEST,DC=LAB |
action_result.parameter.object | string | | CN=SVC-TEST,OU=TEST,DC=TEST,DC=LAB |
action_result.data.\*.destination_container | string | | OU=TEST,DC=TEST,DC=LAB |
action_result.data.\*.source_object | string | | CN=SVC-TEST,OU=TEST,DC=TEST,DC=LAB |
action_result.summary.moved | string | | True |
action_result.message | string | | Moved: True |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'run query'

Query Active Directory LDAP

Type: **investigate** \
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
action_result.status | string | | success failed |
action_result.parameter.attributes | string | | sAMAccountName |
action_result.parameter.filter | string | | (sAMAccountName=\*) |
action_result.parameter.search_base | string | | ou=test,dc=test,dc=lab |
action_result.data.\*.entries.\*.attributes | string | | |
action_result.data.\*.entries.\*.attributes.samaccountname | string | | SVC-TEST |
action_result.data.\*.entries.\*.dn | string | | CN=SVC-TEST,OU=TEST,DC=TEST,DC=LAB |
action_result.summary.total_objects | numeric | | 1 |
action_result.message | string | | Total objects: 1 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'get attributes'

Get attributes of various principals

Type: **investigate** \
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
action_result.status | string | | success failed |
action_result.parameter.attributes | string | | ObjectGUID |
action_result.parameter.principals | string | | SVC-TEST;defaultaccount |
action_result.data.\*.entries.\*.attributes | string | | |
action_result.data.\*.entries.\*.attributes.objectGUID | string | | {a6c536dd-2487-41dd-8524-0037342505da} |
action_result.data.\*.entries.\*.dn | string | | CN=SVC-TEST,OU=test,DC=TEST,DC=LAB |
action_result.summary | string | | |
action_result.summary.total_objects | numeric | | 2 |
action_result.message | string | | Total objects: 2 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'set attribute'

Add, delete, or replace an attribute of a user

Type: **generic** \
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use_samaccountname** | optional | Use sAMAccountName instead of distinguishedName | boolean | |
**user** | required | User whose attributes are to be modified | string | `user name` |
**attribute** | required | The attribute to modify (add/delete/replace) | string | |
**value** | optional | Attribute value | string | |
**action** | required | Semi-colon separated list of attributes to collect | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.action | string | | REPLACE |
action_result.parameter.attribute | string | | mail |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.parameter.user | string | `user name` | Cn=SVC-TEST,OU=TEST,DC=TEST,DC=LAB |
action_result.parameter.value | string | | svc_test@test.com |
action_result.data.\*.message | string | | Success |
action_result.summary.summary | string | | Successfully Set Attributes |
action_result.message | string | | Summary: Successfully Set Attributes |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'rename object'

Rename the object

Type: **generic** \
Read only: **False**

When 'use_samaccountname' is false, the 'object' parameter should include the distinguishedName. Otherwise, use the sAMAccountName. For the 'new_name' parameter, append the new name to the attribute name. For example, to rename a user, use 'cn=New_user_name'; for an OU, use 'ou=New_OU_name'.

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**object** | required | The object to be renamed | string | `user name` |
**use_samaccountname** | optional | Use sAMAccountName instead of distinguishedName | boolean | |
**new_name** | required | New name for the object | string | `user name` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.object | string | `user name` | cn=test user,ou=test,dc=test,dc=test,dc=com |
action_result.parameter.use_samaccountname | boolean | | True False |
action_result.parameter.new_name | string | `user name` | cn=new name |
action_result.status | string | | success failed |
action_result.data.\*.message | string | | Success |
action_result.summary.summary | string | | Successfully Renamed Object |
action_result.message | string | | Summary: Successfully Renamed Object |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2025 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
