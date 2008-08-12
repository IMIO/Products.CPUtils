import logging
logger = logging.getLogger('contacts')

def getContacts(self):
    #return the list of contacts
    return self.portal_properties.contacts_properties.contacts

def getSubjectsByContact(self, contact):
    #we check if the contact exist
    contacts = self.getContacts()
    if contact not in contacts:
        return None
    else:
        #we get the subjects that are at the same possition in the list as the contact
        #first : calculate the position of the contact
        i = 0
        contacts = list(contacts)
        try:
            i = contacts.index(contact)
        except Exception, errormsg:
            logger.error("contact '%s' not found in contacts '%s'"%(contact, contacts))
            return None
        
        #we know the contact position, get the subjects
        list_subjects = ''
        try:
            list_subjects = self.portal_properties.contacts_properties.subjects[i]
        except Exception, errmsg:
            pass

        #we split the subjects using '|' as separator
        subjects_table = []
        for subject in list_subjects.split('|'):
            subject = subject.strip()
            if subject:
                subjects_table.append(subject)
        return subjects_table

def getLink(self, contact):
    #we check if the contact exist
    contacts = self.getContacts()
    if contact not in contacts:
        return None
    else:
        #we get the link that is at the same possition in the list as the contact
        #first : calculate the position of the contact
        i = 0
        contacts = list(contacts)
        try:
            i = contacts.index(contact)
        except Exception, errormsg:
            logger.error("contact '%s' not found in contacts '%s'"%(contact, contacts))
            return None

        #we know the contact position, get the emails
        link = ''
        try:
            link = self.portal_properties.contacts_properties.links[i]
        except Exception, errmsg:
            pass

        return link.strip()

def getEmailAddress(self, contact):
    #if contact is None, we get the 'contact' from the REQUEST
    #we check if the contact exist
    contacts = self.getContacts()
    if contact not in contacts:
        return None
    else:
        #we get the emails that are at the same position in the list as the contact
        #first : calculate the position of the contact
        i = 0
        contacts = list(contacts)
        try:
            i = contacts.index(contact)
        except Exception, errormsg:
            logger.error("contact '%s' not found in contacts '%s'"%(contact, contacts))
            return None

        #we know the contact position, get the emails
        list_emails = ''
        try:
            list_emails = self.portal_properties.contacts_properties.emails[i]
        except Exception, errmsg:
            pass

        #we split the emails using '|' as separator
        emails_table = []
        for email in list_emails.split('|'):
            email = email.strip()
            if email:
                emails_table.append(email)

        #we check if the manager has to receive the message too
        manager_email = self.portal_properties.contacts_properties.managerEmailAddress.strip()
        if self.portal_properties.contacts_properties.sendToManager:
            emails_table.append(manager_email)
        elif not emails_table and manager_email:
            #if no email exist for the contact but a manager email is defined, it is used by default
            emails_table.append(manager_email)
        
        return emails_table