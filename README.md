[comment]: # "Auto-generated SOAR connector documentation"
# AD LDAP

Publisher: Splunk  
Connector Version: 2\.2\.0  
Product Vendor: Splunk  
Product Name: Active Directory LDAP  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 5\.3\.5  

App specifically designed for interacting with Microsoft Active Directory's LDAP Implementation

[comment]: # " File: README.md"
[comment]: # "     Copyright (c) 2021-2022 Splunk Inc."
[comment]: # "     Licensed under the Apache License, Version 2.0 (the 'License');"
[comment]: # "     you may not use this file except in compliance with the License."
[comment]: # "     You may obtain a copy of the License at"
[comment]: # ""
[comment]: # "       http://www.apache.org/licenses/LICENSE-2.0"
[comment]: # ""
[comment]: # "     Unless required by applicable law or agreed to in writing, software distributed under"
[comment]: # "     the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,"
[comment]: # "     either express or implied. See the License for the specific language governing permissions"
[comment]: # "     and limitations under the License."
[comment]: # ""
## App Information

-   This LDAP application utilizes the LDAP3 library for Python. This was chosen, in part, due to
    the pythonic design of the library and the quality of the documentation. Both SSL and TLS are
    supported.
-   Please make sure to view additional documentation for this app on our [GitHub Open Source
    Repo!](https://github.com/phantomcyber/phantom-apps/tree/next/Apps/phadldap#readme)

## LDAP Ports Requirements (Based on Standard Guidelines of [IANA ORG](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml) )

-   LDAP(service) TCP(transport protocol) - 389
-   LDAP(service) UDP(transport protocol) - 389
-   LDAP(service) TCP(transport protocol) over TLS/SSL (was sldap) - 636
-   LDAP(service) UDP(transport protocol) over TLS/SSL (was sldap) - 636

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

-   Need to install the certificate on the server

      

    -   Upload the SSL certificate on the server
    -   Go to /opt/phantom/bin and execute the import_cert.py script using command:  
        **phenv python3 import_cert.py -i "path_of_certificate_on_server"**

-   Go to etc/hosts using the root user. Assign the domain to IP to use the SSL certificate

**Note:** For reference: [Splunk
Docs](https://docs.splunk.com/Documentation/SOARonprem/latest/Admin/AddOrRemoveCertificates)

## Run Query Action

This action provides the user the ability to run generic queries with the LDAP syntax. The action
takes a filter (in LDAP syntax), an optional search base to search within, and specific attributes
that you would like to return.

-   Common AD LDAP Run Query Examples

      

    -   Get Users belonging to a specific OU, Container, or Group

          

        -   filter = (samaccountname=\*)
        -   attributes = samaccountname;mail
        -   search_base = distinguishedNameOfOU/Container/Group

    -   List Group Names that a User belongs to

          

        -   filter = (&(member=distinguishedNameOfUserHERE)(objectClass=group))
        -   attributes = name

    -   Return results if mail attribute is present OR sAMAccountName matches '\*admin\*'

          

        -   filter = (\|(mail=\*)(samaccountname=\*admin\*))
        -   attributes = samaccountname;mail;userprincipalname;distinguishedname

    -   If you would like to learn more about LDAP Filter Syntax, check out this [Microsoft
        Wiki](https://social.technet.microsoft.com/wiki/contents/articles/5392.active-directory-ldap-syntax-filters.aspx)

  


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Active Directory LDAP asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**server** |  required  | string | The Active Directory Server hostname, IP, or VIP for binding
**username** |  required  | string | The username with which to bind to LDAP
**password** |  required  | password | The password for the binding user
**force\_ssl** |  optional  | boolean | Force the use of SSL protocol\. Note that some actions are not possible without secure binding\!
**validate\_ssl\_cert** |  optional  | boolean | Select if you want to validate the LDAP SSL certificate
**ssl\_port** |  required  | numeric | The port to bind for SSL \(default 636\)

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[add group members](#action-add-group-members) - Adds one or more Active Directory objects to one or more groups  
[remove group members](#action-remove-group-members) - Removes one or more Active Directory objects from one or more groups  
[unlock account](#action-unlock-account) - Unlocks a locked Active Directory account  
[disable account](#action-disable-account) - Disables an Active Directory account  
[enable account](#action-enable-account) - Enables a disabled Active Directory account  
[reset password](#action-reset-password) - Resets the password of a user, requiring the user to change password at next login  
[set password](#action-set-password) - Set a user's password  
[move object](#action-move-object) - Moves an entry in Active Directory  
[run query](#action-run-query) - Query Active Directory LDAP  
[get attributes](#action-get-attributes) - Get attributes of various principals  
[set attribute](#action-set-attribute) - Add, delete, or replace an attribute of a user  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'add group members'
Adds one or more Active Directory objects to one or more groups

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use\_samaccountname** |  optional  | Specify members AND groups as sAMAccountName\(s\) instead of distinguishedName\(s\) \(note\: member AND groups will use sAMAccountName if selected\) | boolean | 
**members** |  required  | Semi\-colon \(';'\) separated list of users\. If 'use samaccountname' is false, then these must be distinguishedName\(s\) | string | 
**groups** |  required  | Semi\-colon \(';'\) separated list of groups to which the members will be added\. If 'use samaccountname' is false, then these must be distinguishedName\(s\) | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.groups | string | 
action\_result\.parameter\.members | string | 
action\_result\.parameter\.use\_samaccountname | boolean | 
action\_result\.data\.\*\.function | string | 
action\_result\.data\.\*\.group | string | 
action\_result\.data\.\*\.member | string | 
action\_result\.summary | string | 
action\_result\.summary\.found\_user\_records | numeric | 
action\_result\.summary\.requested\_user\_records | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'remove group members'
Removes one or more Active Directory objects from one or more groups

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use\_samaccountname** |  optional  | Specify members AND groups as sAMAccountName\(s\) instead of distinguishedName\(s\) | boolean | 
**members** |  required  | Semi\-colon \(';'\) separated list of users\. If 'use samaccountname' is false, then these must be distinguishedName\(s\) | string | 
**groups** |  required  | Semi\-colon \(';'\) separated list of groups from which the members will be removed\. If 'use samaccountname' is false, then these must be distinguishedName\(s\) | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.groups | string | 
action\_result\.parameter\.members | string | 
action\_result\.parameter\.use\_samaccountname | boolean | 
action\_result\.data\.\*\.function | string | 
action\_result\.data\.\*\.group | string | 
action\_result\.data\.\*\.member | string | 
action\_result\.summary | string | 
action\_result\.summary\.found\_user\_records | numeric | 
action\_result\.summary\.requested\_user\_records | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'unlock account'
Unlocks a locked Active Directory account

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use\_samaccountname** |  optional  | Use sAMAccountName for user instead of distinguishedName\(s\) | boolean | 
**user** |  required  | Specify the user to unlock\. If 'use samaccountname' is false, then this must be the user's distinguishedName | string |  `user name` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.use\_samaccountname | boolean | 
action\_result\.parameter\.user | string |  `user name` 
action\_result\.data\.\*\.samaccountname | string | 
action\_result\.data\.\*\.unlocked | boolean | 
action\_result\.data\.\*\.user\_dn | string | 
action\_result\.summary | string | 
action\_result\.summary\.unlocked | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'disable account'
Disables an Active Directory account

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use\_samaccountname** |  optional  | Specify sAMAccountName instead of distinguishedName | boolean | 
**user** |  required  | Specify the user to disable\. If 'use samaccountname' is false, then this must be the user's distinguishedName | string |  `user name` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.use\_samaccountname | boolean | 
action\_result\.parameter\.user | string |  `user name` 
action\_result\.data\.\*\.starting\_status | string | 
action\_result\.data\.\*\.user\_dn | string | 
action\_result\.summary\.account\_status | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'enable account'
Enables a disabled Active Directory account

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use\_samaccountname** |  optional  | Specify sAMAccountName instead of distinguishedName | boolean | 
**user** |  required  | Specify the user to enable\. If 'use samaccountname' is false, then this must be the user's distinguishedName | string |  `user name` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.use\_samaccountname | boolean | 
action\_result\.parameter\.user | string |  `user name` 
action\_result\.data\.\*\.starting\_status | string | 
action\_result\.data\.\*\.user\_dn | string | 
action\_result\.summary\.account\_status | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'reset password'
Resets the password of a user, requiring the user to change password at next login

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use\_samaccountname** |  optional  | Use sAMAccountName instead of distinguishedName | boolean | 
**user** |  required  | User whose attributes are to be modified | string |  `user name` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.use\_samaccountname | boolean | 
action\_result\.parameter\.user | string |  `user name` 
action\_result\.data\.\*\.reset | numeric | 
action\_result\.data\.\*\.samaccountname | string | 
action\_result\.data\.\*\.user\_dn | string | 
action\_result\.summary\.reset | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'set password'
Set a user's password

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use\_samaccountname** |  optional  | Specify sAMAccountName instead of distinguishedName | boolean | 
**user** |  required  | Specify the user whose password will be set\. If 'use samaccountname' is false, then this must be the user's distinguishedName | string |  `user name` 
**password** |  required  | New password | string | 
**confirm\_password** |  required  | Re\-type the password | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.confirm\_password | string | 
action\_result\.parameter\.password | string | 
action\_result\.parameter\.use\_samaccountname | boolean | 
action\_result\.parameter\.user | string |  `user name` 
action\_result\.data\.\*\.samaccountname | string | 
action\_result\.data\.\*\.set | boolean | 
action\_result\.data\.\*\.user\_dn | string | 
action\_result\.summary | string | 
action\_result\.summary\.set | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'move object'
Moves an entry in Active Directory

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**object** |  required  | Specify the distinguishedName to move | string | 
**destination\_ou** |  required  | The distinguishedName of the OU the specified object will move to | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.destination\_ou | string | 
action\_result\.parameter\.object | string | 
action\_result\.data\.\*\.destination\_container | string | 
action\_result\.data\.\*\.source\_object | string | 
action\_result\.summary\.moved | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'run query'
Query Active Directory LDAP

Type: **investigate**  
Read only: **True**

This action flexibly supports querying Active Directory using LDAP syntax\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**filter** |  required  | The LDAP filter \(must be in LDAP Syntax\) | string | 
**search\_base** |  optional  | The search base to use in its distinguishedName format\. If not specified, the 'defaultNamingContext' will be used | string | 
**attributes** |  required  | Semi\-colon separated list of attributes to collect \(e\.g\. sAMAccountName;mail\) | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.attributes | string | 
action\_result\.parameter\.filter | string | 
action\_result\.parameter\.search\_base | string | 
action\_result\.data\.\*\.entries\.\*\.attributes | string | 
action\_result\.data\.\*\.entries\.\*\.attributes\.samaccountname | string | 
action\_result\.data\.\*\.entries\.\*\.dn | string | 
action\_result\.summary\.total\_objects | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'get attributes'
Get attributes of various principals

Type: **investigate**  
Read only: **True**

This action takes any number of principals \(sAMAccountName, distinguishedName, or userprincipalname\) and returns requested attributes\. Separate with semi\-colon \(';'\)\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**principals** |  required  | The semi\-colon separated principals\. These can be sAMAccountName, userprincipalname, or distinguishedName | string | 
**attributes** |  required  | Semi\-colon separated list of attributes to collect | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.attributes | string | 
action\_result\.parameter\.principals | string | 
action\_result\.data\.\*\.entries\.\*\.attributes | string | 
action\_result\.data\.\*\.entries\.\*\.attributes\.objectGUID | string | 
action\_result\.data\.\*\.entries\.\*\.dn | string | 
action\_result\.summary | string | 
action\_result\.summary\.total\_objects | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'set attribute'
Add, delete, or replace an attribute of a user

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**use\_samaccountname** |  optional  | Use sAMAccountName instead of distinguishedName | boolean | 
**user** |  required  | User whose attributes are to be modified | string |  `user name` 
**attribute** |  required  | The attribute to modify \(add/delete/replace\) | string | 
**value** |  optional  | Attribute value | string | 
**action** |  required  | Semi\-colon separated list of attributes to collect | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.action | string | 
action\_result\.parameter\.attribute | string | 
action\_result\.parameter\.use\_samaccountname | boolean | 
action\_result\.parameter\.user | string |  `user name` 
action\_result\.parameter\.value | string | 
action\_result\.data\.\*\.message | string | 
action\_result\.summary\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 