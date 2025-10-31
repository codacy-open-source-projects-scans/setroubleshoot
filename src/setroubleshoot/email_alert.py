from __future__ import absolute_import
# Authors: John Dennis <jdennis@redhat.com>
#
# Copyright (C) 2006,2007,2008 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

__all__ = ['email_alert',
           ]

import syslog
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

from setroubleshoot.config import get_config
from setroubleshoot.util import *

email_addr_re = re.compile(r'^\s*([^@ \t]+)(@([^@ \t]+))?\s*$')


def parse_email_addr(addr):
    match = email_addr_re.search(addr)
    user = None
    domain = None
    if match:
        user = match.group(1)
        domain = match.group(3)
    return (user, domain)


def email_alert(siginfo, to_addrs):
    smtp_host = get_config('email', 'smtp_host')
    smtp_port = get_config('email', 'smtp_port', int)
    from_address = get_config('email', 'from_address')

    from_user, from_domain = parse_email_addr(from_address)
    if from_user is None:
        from_user = "SELinuxTroubleshoot"
    if from_domain is None:
        from_domain = get_hostname()
    from_address = '%s@%s' % (from_user, from_domain)

    log_debug("alert smtp=%s:%d  -> %s" % (smtp_host, smtp_port, ','.join(to_addrs)))

    siginfo.update_derived_template_substitutions()
    summary = siginfo.substitute(siginfo.summary())
    subject = '[%s] %s' % (get_config('email', 'subject'), summary)
    text = siginfo.format_text() + siginfo.format_details()

    email_msg = MIMEMultipart('alternative')
    email_msg['Subject'] = subject
    email_msg['From'] = from_address
    email_msg['To'] = ', '.join(to_addrs)
    email_msg['Date'] = formatdate()

    email_msg.attach(MIMEText(text))

    if not get_config('email', 'use_sendmail', bool):
        import smtplib
        try:
            smtp = smtplib.SMTP(smtp_host, smtp_port)
            smtp.sendmail(from_address, to_addrs, email_msg.as_string())
            smtp.quit()
        except smtplib.SMTPException as e:
            syslog.syslog(syslog.LOG_ERR, "email failed: %s" % e)
    else:
        import subprocess
        try:
            subprocess.run(["sendmail", "-t", "-oi"], input=email_msg.as_string(), check=True, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            syslog.syslog(syslog.LOG_ERR, "email failed: %s" % e)

#-----------------------------------------------------------------------------

if __name__ == "__main__":
    xmldata = """
<?xml version="1.0" encoding="utf-8"?>
<sigs version="3.0">
  <signature_list>
    <siginfo>
      <audit_event>
        <event_id host="P1" milli="205" seconds="1643896441" serial="1401"/>
        <records>
          <audit_record record_type="AVC">
            <body_text>avc:  denied  { write } for  pid=61664 comm="passwd" path="/root/output.txt" dev="dm-1" ino=16778525 scontext=unconfined_u:unconfined_r:passwd_t:s0-s0:c0.c1023 tcontext=unconfined_u:object_r:admin_home_t:s0 tclass=file permissive=0</body_text>
            <event_id host="P1" milli="205" seconds="1643896441" serial="1401"/>
          </audit_record>
        </records>
      </audit_event>
      <environment version="1.0">
        <enforce>Enforcing</enforce>
        <hostname>P1</hostname>
        <kernel>5.16.0-60.fc36.x86_64 x86_64</kernel>
        <local_policy_rpm>selinux-policy-targeted-35.11-1.fc35.noarch</local_policy_rpm>
        <platform>Fedora release 35 (Thirty Five)</platform>
        <policy_rpm>selinux-policy-targeted-35.11-1.fc35.noarch</policy_rpm>
        <policy_type>targeted</policy_type>
        <policyvers>33</policyvers>
        <selinux_enabled>True</selinux_enabled>
        <selinux_mls_enabled>True</selinux_mls_enabled>
        <uname>Linux P1 5.16.0-60.fc36.x86_64 #1 SMP PREEMPT Mon Jan 10 13:00:29 UTC 2022 x86_64 x86_64</uname>
      </environment>
      <first_seen_date>2022-02-03T13:48:54Z</first_seen_date>
      <last_seen_date>2022-02-03T13:54:01Z</last_seen_date>
      <level>yellow</level>
      <local_id>b0826257-4747-4257-a6aa-a890a7abd608</local_id>
      <plugin_list>
        <plugin>
          <analysis_id>catchall</analysis_id>
          <args>
            <arg>0</arg>
            <arg>file</arg>
            <arg>/root/output.txt</arg>
          </args>
        </plugin>
      </plugin_list>
      <report_count>3</report_count>
      <scontext mls="s0-s0:c0.c1023" role="unconfined_r" type="passwd_t" user="unconfined_u"/>
      <sig version="4.0">
        <access>
          <operation>write</operation>
        </access>
        <host>P1</host>
        <scontext mls="s0-s0:c0.c1023" role="unconfined_r" type="passwd_t" user="unconfined_u"/>
        <tclass>file</tclass>
        <tcontext mls="s0" role="object_r" type="admin_home_t" user="unconfined_u"/>
      </sig>
      <source>passwd</source>
      <spath>passwd</spath>
      <tclass>file</tclass>
      <tcontext mls="s0" role="object_r" type="admin_home_t" user="unconfined_u"/>
      <tpath>/root/output.txt</tpath>
      <users>
      </users>
    </siginfo>
  </signature_list>
  <users>
  </users>
</sigs>
    """
    import os
    import setroubleshoot.signature
    sigs = setroubleshoot.signature.SEFaultSignatureSet()
    sigs.read_xml(xmldata, 'sigs')
    email_alert(sigs.signature_list[0], [os.getlogin() + "@localhost"])
