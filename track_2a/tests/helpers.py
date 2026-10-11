from fpdf import FPDF

PAGES = [
    "Seite eins. Allgemeine Informationen zur Abstimmung.",
    "Der Bundesrat empfiehlt, die Initiative abzulehnen, weil sie die Stabilität der Schweiz gefährdet. "
    "Seit 2002 ist die Bevölkerung um rund 1,7 Millionen Personen gewachsen.",
    "Zusammenfassung: Der Bundesrat empfiehlt, die Initiative abzulehnen, weil sie die Stabilität der Schweiz gefährdet.",
]


def make_pdf(path, pages=PAGES):
    pdf = FPDF()
    pdf.set_font("Helvetica", size=11)
    for t in pages:
        pdf.add_page()
        pdf.multi_cell(0, 6, t)
    pdf.output(str(path))
