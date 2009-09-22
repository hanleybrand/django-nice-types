#!/usr/bin/env python
from __future__ import with_statement
from docutils import writers, nodes
import textwrap

class indented_wrapped_text(object):                                                  
    def __init__(self, indent=0):
        self.indent = indent
        self.text = u''
        self.current_line = u''

    def do_indent(self, i):
        self.indent += i

    def newline(self):
        if self.current_line:
            self.text += self.current_line
        self.text += "\n"
        self.current_line = u''

    def append(self, t):
        if not self.current_line:
            self.current_line = " " * self.indent

        self.current_line += t
        if self.current_line.find("\n") != -1:
            lines = self.current_line.replace("\n", "\n" + " "*self.indent).split("\n")
            for l in lines[:-1]:
                r, c = self.wrap_line(l)
                self.text += (r + c + "\n")
            self.current_line = lines[-1]
        rem, self.current_line = self.wrap_line(self.current_line)
        self.text += rem

    def __repr__(self):
        return unicode(self)

    def wrap_line(self, line):
        remainder = u''
        old_len = len(line)
        while len(line) > 79:
            i = line.rfind(" ", 0, 80)
            remainder += line[:i]
            line = ("\n" + " "*self.indent) + line[i:].lstrip()
            if len(line) == old_len:
                break
            old_len = len(line)
        return remainder, line

    def __unicode__(self):
        return self.text + self.current_line

def strip_common_prefix(lines):
    prefix = lines[0]
    for l in lines[1:]:
        if not l:
            continue
        for i, char in enumerate(prefix):
            if i >= len(l):
                prefix = l
                break
            if l[i] != char:
                prefix = prefix[:i]
                break
    if not prefix:
        return lines
    lines = [l.replace(prefix, "", 1) for l in lines]
    return strip_common_prefix(lines)

HEADING_UNDERLINE = ['', '=', '-', '~', '+']
class EmailVisitor(nodes.NodeVisitor):
    def visit_document(self, n):
        self.section_depth = 0
        self.plaintext = indented_wrapped_text()
        self.html = u''

        self.p = u''
        self.listnumber = []
        self.lineblocks = []

    def unknown_visit(self, n):
        print "Unknown visit to %s" % n.__class__.__name__
        return
    def unknown_departure(self, n):
        return

    def asplaintext(self):
        return unicode(self.plaintext)

    def ashtml(self):
        return self.html

    def asemail(self):
        boundary = u"000e0cd2bf9c220f42046455a3b1"
        txt = []
        txt.append(u"Content-Type: multipart/alternative; boundary=%s\n" % boundary)
        txt.append(u"\n--%s\n" % boundary)
        txt.append(u"Content-Type: text/plain; charset=UTF-8\n")
        txt.append(u"Content-Transfer-Encoding: 7bit\n")

        txt.append(self.asplaintext().encode('utf-7'))

        txt.append(u"\n--%s\n" % boundary)
        txt.append(u"Content-Type: text/html; charset=UTF-8\n")
        txt.append(u"Content-Transfer-Encoding: 7bit\n")

        txt.append(self.ashtml().encode('utf-7'))

        txt.append(u"\n--%s\n" % boundary)

        output = u''.join(txt)
        return output.encode('utf-8')

    def visit_enumerated_list(self, n):
        self.listnumber.append(int(n.get('start', 1)))
        self.plaintext.do_indent(1)
        self.html += "<ol>"

    def depart_enumerated_list(self, n):
        self.listnumber.pop()
        self.plaintext.do_indent(-1)
        self.plaintext.newline()
        self.html += "</ol>"

    def visit_list_item(self, n):
        self.html += "<li>"

        self.plaintext.append(" %s. " % (str(self.listnumber[-1]).rjust(2),))
        self.plaintext.do_indent(5)
        self.listnumber[-1] += 1

    def depart_list_item(self, n):
        self.plaintext.do_indent(-5)
        self.html += "</li>"

    def visit_section(self, n):
        self.plaintext.append("\n")
        self.section_depth += 1
        self.html += "<div class='section'>"

    def depart_section(self, n):
        self.html += "</div>"
        self.section_depth -= 1

    def visit_Text(self, n):
        self.p += n.astext()
        self.html += n.astext()

    def visit_transition(self, n):
        self.html += "<hr>"
        self.plaintext.newline()
        self.plaintext.append("-"*20)
        self.plaintext.newline()

    def visit_title(self, n):
        self.p = u''
        self.html += u"<h%d>" % (self.section_depth + 2)

    def depart_title(self, n):
        self.plaintext.append(self.p + "\n" +  HEADING_UNDERLINE[self.section_depth]*len(self.p))
        self.plaintext.newline()
        self.plaintext.newline()
        self.html += u"</h%d>" % (self.section_depth + 2)


    def visit_paragraph(self, n):
        self.html += u"<div>"
        self.p = u''

    def visit_literal_block(self, n):
        self.html += u"<pre style=\"white-space: -moz-pre-wrap; white-space: -pre-wrap; white-space: -o-pre-wrap; white-space: pre-wrap; word-wrap: break-word;\">"
        self.old_html = self.html
        self.p = u''

    def visit_line(self, n):
        self.p = u''
        self.old_html = self.html

    def depart_line(self, n):
        self.html = self.old_html + self.p + "<br>"
        self.plaintext.append(self.p + "\n")

    def depart_paragraph(self, n):
        self.html += u"</div><br/>"
        self.plaintext.append(self.p)
        self.plaintext.newline()
        self.plaintext.newline()

    def depart_literal_block(self, n):
        lines = self.p.split("\n")
        lines = "\n".join(strip_common_prefix(lines))

        self.html = self.old_html + lines + u"</pre><br/>"

        self.plaintext.do_indent(5)
        self.plaintext.append(lines)
        self.plaintext.do_indent(-5)
        self.plaintext.newline()
        self.plaintext.newline()

    def visit_reference(self, n):
        self.html += u"<a href='%s'>" % n['refuri']

    def depart_reference(self, n):
        self.html += u"</a>"

    def visit_strong(self, s):
    #    self.p += u"*"
        self.html += u"<span style='font-weight: bold'>"

    def depart_strong(self, s):
    #    self.p += u"*"
        self.html += u"</span>"

def rst2email(text=None, rst_file=None):
    import docutils.parsers.rst
    import docutils.utils
    if rst_file:
        text = rst_file.read()

    parser = docutils.parsers.rst.Parser()
    d = docutils.utils.new_document("")
    d.settings.tab_width = 4
    d.settings.pep_references = False
    d.settings.rfc_references = False

    parser.parse(text, d)
    visitor = EmailVisitor(d)
    d.walkabout(visitor)

    return visitor

if __name__ == "__main__":
    import sys
    from contextlib import closing
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hepi:o:")
    except getopt.GetoptError, err:
        print str(err)
        print "Usage: %s -i <input> -o <output> [-hep]"
        sys.exit(1)

    inf = outf = "-"
    output = 'asplaintext'
    for k, v in opts:
        if k == '-i':
            inf = v
        elif k == '-o':
            outf = v
        elif k == '-h':
            output = 'ashtml'
        elif k == '-e':
            output = 'asemail'
        elif k == '-p':
            output = 'asplaintext'
        else:
            raise Exception

    with closing(sys.stdin if inf == '-' else open(inf, 'r')) as f:
        txt = f.read().decode('utf-8')
    
    visitor = rst2email(txt)

    output_fun = getattr(visitor, output)
    with closing(sys.stdout if outf == '-' else open(outf, 'r')) as f:
        f.write(output_fun().encode('utf-8'))


