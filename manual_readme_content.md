[comment]: # " File: README.md"
[comment]: # "     Copyright (c) 2021-2024 Splunk Inc."
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

          

        -   filter = (|(mail=\*)(samaccountname=\*admin\*))
        -   attributes = samaccountname;mail;userprincipalname;distinguishedname

    -   If you would like to learn more about LDAP Filter Syntax, check out this [Microsoft
        Wiki](https://social.technet.microsoft.com/wiki/contents/articles/5392.active-directory-ldap-syntax-filters.aspx)


    - If any of the following special characters must appear in the query filter as literals, they must be replaced by the listed escape sequence.


        | ASCII character | Escape sequence substitute |
        |-----------------|----------------------------|
        | *               | \2a                      |
        | (               | \28                      |
        | )               | \29                      |
        | \               | \5c                      |
        | NUL             | \00                      |

        Example: To find all objects where the common name is "James Jim*) Smith", the LDAP filter would be: (cn=James Jim\2A\29 Smith)
