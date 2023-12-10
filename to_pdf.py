import fpdf
import math

def to_pdf(Sr_top, AB_top, num_of_ABs, num_of_Srs, stats, num_of_stds, semester, objval, report_file_name):

    pdf = fpdf.FPDF(format='letter')
    pdf.add_page()
    pdf.set_font("Arial", size=20)
    
    pdf.write(5, 'Assignment Statistics')
    pdf.ln()
    pdf.ln()
    
    
    pdf.set_font("Arial", size=12)
    pdf.write(5, 'Natural log of Objective function: ~' + str(round(math.log(objval), 2)))
    pdf.ln()
    pdf.ln()
    pdf.set_font("Arial", size=15)
    pdf.write(5, 'Number of students who got assigned to their ith choice:')
    pdf.ln()
    pdf.ln()

    pdf.set_font("Arial", size=12)

    keys = list(stats.keys())
    keys.sort()
    
    for key in keys:
        output = 'Choice number ' + str(key) + ': ' + str(int(stats.get(key))) + '/' + str(num_of_stds)
        pdf.write(5, output)
        pdf.ln()

    pdf.ln()
    pdf.set_font("Arial", size=15)
    pdf.write(5, 'Number of AB students who got their top choice:')
    pdf.set_font("Arial", size=12)
    pdf.ln()
    pdf.ln()
    pdf.write(5, str(AB_top) + '/' + str(num_of_ABs))
    if semester == 'Spring':
        pdf.ln()
        pdf.ln()
        pdf.set_font("Arial", size=15)
        pdf.write(5, 'Number of Senior students who got their top choice:')
        pdf.set_font("Arial", size=12)
        pdf.ln()
        pdf.ln()
        pdf.write(5, str(Sr_top) + '/' + str(num_of_Srs))
    pdf.output(report_file_name) 