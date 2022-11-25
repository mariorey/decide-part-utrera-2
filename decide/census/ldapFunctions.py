from ldap3 import Server, Connection, ALL_ATTRIBUTES
import re

class LdapCensus:
    def ldapConnection(self, urlServer, auth, psw):
        """This method establishes a connection with the LDAP server passed by parameters, 
        the object address object is returned at the end.
    
        Args:
            urlServer: server URL containing the port in use.
            auth: the account of the user to log in for simple bind.
            psw: the password of the user.
        """ 
        server = Server(urlServer)
        conn = Connection(server, auth, psw, auto_bind=True)
        return conn

    def ldapGroups(self, LdapUrl, auth, psw, branch):
        """This method calls ldapConnectionMethod to establish a connection and then do a search for 
        the branch indicated where the users to be added in the census are located
    
        Args:
            LdapUrl: server URL containing the port in use.
            auth: the account of the user to log in for simple bind.
            psw: the password of the user.
            branch: branch of the group whose members we want to add to the census.
        """ 
        conn = LdapCensus().ldapConnection(LdapUrl, auth, psw)
        conn.search(search_base=branch, search_filter='(objectclass=*)', attributes=[ALL_ATTRIBUTES])
        ldapList = []
        for entries in conn.entries:
            text = str(entries)
            group = re.findall('uid=(.+?),', text, re.DOTALL)
            for element in group:
                if group and ldapList.count(element) == 0:            
                    ldapList.append(element)
        return ldapList