import csv
import os
import queue
import sys
import getopt
from datetime import datetime
import copy

inputfile = ''
outputfile = ''


def extract_date(inp: str) -> str:
    p = inp.find(' ', 1)
    dt = inp[:p]
    return dt


def extract_time(inp: str) -> str:
    p = inp.find(' ', 1)
    tm = inp[p + 1:]
    return tm


def onlyValidChars(s) -> str:
    rslt = ''
    i = 0
    n = len(s)
    while i < n:
        c = ord(s[i])
        if (c > 31) and (c < 127):
            rslt = rslt + s[i]
        i = i + 1
    return rslt


def only_printable(s) -> str:
    result = ''
    i = 0
    while i < len(s):
        c = ord(s[i])
        if (c > 31) and (c < 127):
            result = result + s[i]
        i = i + 1
    return result


def load_csv(inputFile: str):
    _d1 = []
    with open(inputFile, 'r') as f:
        firstline = f.readline()
        firstline = firstline.replace('\0', '')
        firstline = firstline.replace('\n', '')
        firstline = firstline.replace('\r', '')
        firstline = firstline.strip()
        row1 = firstline.split('\t')

        i = 0
        n = len(row1)
        columns = []
        while i < n:
            s = only_printable(row1[i].strip())
            s = s.replace(' ', '_')
            if len(s) > 0:
                columns.append(s)
            i = i + 1

        print(columns)
    #

        lines = []
        try:
            NotDone = True
            while NotDone:  # Python 3.8
                try:
                    oneline = f.readline()
                    if len(oneline) < 1:
                        NotDone = False
                        break
                    oneline = oneline.replace('\0', '')
                    oneline = oneline.replace('\n', '')
                    oneline = oneline.replace('\r', '')
                    oneline = oneline.strip()
                    if len(oneline) > 3:
                        lines.append(oneline)
                except Exception as e:
                    print(f'Error reading line: {e}')
        except:
            # print queue items
            pass

        f.close()

    _results = []
    i = 0
    for line in lines:
        l = line.replace('\0', '')
        i += 1
        if i > 1 and len(l) > 5:
            # this is a valid row.
            row = l.split('\t')
            if len(row) == len(columns):
                onerec = {}
                j = 0
                while j < len(columns) - 1:
                    key = columns[j]
                    val = row[j].replace('\n', '')
                    onerec[key] = val
                    if key == 'URL':
                        key = 'domain'
                        val = extract_domain(val)
                        onerec[key] = val
                    if key == 'Time Visited':
                        key = 'month'
                        val = datetime.strptime(val, '%m/%d/%Y %I:%M:%S %p').strftime('%B')
                        onerec[key] = val
                    j += 1
                _results.append(onerec)
    return _results


def remove_non_data_rows(data) -> []:
    url: str
    rslt = []
    for r in data:
        toss = False
        url = r['URL'].lower()

        if url.startswith('file:'):
            toss = True

        if not toss:
            rslt.append(r)
    return rslt


def getargs(arguments):
    def usage(p):
        print(f'Usage: {p} -i <input file> -o <output file> -r <report file>')
        return

    global inputfile
    global outputfile
    global reportfile
    program = arguments[0]
    argv = arguments[1:]
    try:
        opts, args = getopt.getopt(argv, "hi:o:r:", ["ifile=", "ofile=", "report="])
    except getopt.GetoptError:
        usage(program)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage(program)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-r", "--report"):
            reportfile = arg

    if len(inputfile) < 1 or len(outputfile) < 1 or len(reportfile) < 1:
        usage(program)
        sys.exit()

    return


# remove column from data
def remove_column(data, column):
    for row in data:
        try:
            del row[column]
        except:
            pass
    return data


# add month column to data
def add_mdy_columns(data):
    dateval: str
    month: str
    day: str
    year: str
    for row in data:
        dateval = extract_date(row['Visit_Time'])
        month = dateval[:dateval.find('/')]
        day = dateval[dateval.find('/') + 1:dateval.rfind('/')]
        year = dateval[dateval.rfind('/') + 1:]
        row['month'] = int(month)
        row['day'] = int(day)
        row['year'] = int(year)
    return data


# add hour and minute columns to data
def add_hm_columns(data):
    timeval: str
    hour: str
    minute: str
    for row in data:
        timeval = extract_time(row['Visit_Time'])
        hour = timeval[:timeval.find(':')]
        minute = timeval[timeval.find(':') + 1: timeval.rfind(':')]
        if (int(hour) < 12) and (timeval.find("PM") > 0):
            hour = str(int(hour) + 12)
        row['hour'] = int(hour)
        row['minute'] = int(minute)
    return data


def save_csv(data, file):
    def getkeys(row):
        result = []
        for key in row:
            result.append(key)
        return result

    def replace_commas(s):
        result = s.replace(',', '&comma;')
        return result

    outputfile = file + '.csv'

    fieldnames = []
    for row in data:
        fieldnames = getkeys(row)
        break  # only need the first row

    #   with open(file, 'w', newline='') as f:
    with open(outputfile, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', quoting=csv.QUOTE_NONNUMERIC)
        w.writeheader()
        for row in data:
            row['URL'] = replace_commas(row['URL'])
            row['Visited_From'] = replace_commas(row['Visited_From'])
            row['Title'] = replace_commas(row['Title'])
            w.writerow(row)
        f.close()
    return


# save data to html file
def save_html(data, file):
    def getkeys(row):
        result = []
        for key in row:
            result.append(key)
        return result

    def replace_commas(s):
        result = s.replace(',', '&comma;')
        return result

    def generate_styles():
        result = ''
        result += '<style>\n'
        result += 'table, th, td {\n'
        result += '  border: 1px solid black;\n'
        result += '  border-collapse: collapse;\n'
        result += '  overflow: hidden;\n'
        result += '  word-wrap: break-word;\n'
        result += '  table-layout: fixed;\n'
        result += '}\n'
        result += 'th, td {\n'
        result += '  text-align: left;\n'
        result += '  vertical-align: top;\n'
        result += '  text-overflow: ellipsis;\n'
        result += '  white-space: nowrap;\n'
        result += '  max-width: 0;\n'
        result += '}\n'
        result += '#datatable { width: 100%; }\n'
        result += '#datatable tbody tr:hover { background-color: lightgreen; }\n'
        result += '</style>\n'
        return result

    def generate_row_click_function():
        # ref: https://stackoverflow.com/a/53032224
        # ref: https://www.w3schools.com/jsref/coll_table_cells.asp
        result = ''
        result += '<script>\n'
        result += 'function row_click(x) {\n'
        result += '  var s = "";\n'
        result += '  var i = 0;\n'
        result += '  var c = x.cells;\n'
        result += '  var selector = "";\n'
        result += '  for (var i = 0; i < x.cells.length; i++) {\n'
        result += '    try { \n'
        result += '      let j = parseInt(1) + parseInt(i);\n'
        result += '      selector = "body > table > thead > tr > th:nth-child(" + j + ")";\n '
        result += '      s += document.querySelector(selector).innerText + ": ";\n'
        result += '    } catch {}\n'
        result += '    s += c[i].innerHTML + "\\n";\n'
        result += '  }\n'
        result += '  alert(s);\n'
        result += '}\n'
        result += '</script>\n'
        return result

    outputfile = file + '.html'

    fieldnames = []
    for row in data:
        fieldnames = getkeys(row)
        break

    with open(outputfile, 'w', newline='') as f:
        # generate html header
        f.write('<!DOCTYPE html>\n')  # html5
        # '
        f.write('<html>\n')
        f.write('<head>\n')
        title = get_report_title()
        f.write(f'<title>{title}</title>\n')
        f.write(generate_styles())
        f.write('</head>\n')
        f.write('<body>\n')
        f.write(f'<h1>{title}</h1>\n')
        f.write('<table id="datatable">\n')
        f.write('<thead>\n')
        txt = '<tr  >'
        for key in fieldnames:
            width = '8%'
            if key == 'URL' or key == 'Title' or key == 'Visited_From':
                width = '10%'
            if key == 'month' or key == 'day' or key == 'year':
                width = '4%'
            if key == 'hour' or key == 'minute':
                width = '4%'
            txt += f'<th style="width:{width}">{key}</th>'
        f.write(txt)
        f.write('</tr>\n')
        f.write('</thead>\n')

        # generate html body
        f.write('<tbody>\n')
        # generate table rows
        for row in data:
            txt = '<tr onclick="row_click(this)">\n'
            f.write(txt)
            for fieldname in fieldnames:
                txt = f'<td>{row[fieldname]}</td>\n'
                f.write(txt)
            txt = '</tr>\n'
            f.write(txt)
        txt = '</table>\n'
        f.write(txt)
        txt = '</body>\n'
        f.write(txt)
        txt = generate_row_click_function()
        f.write(txt)
        txt = '</html>\n'
        f.write(txt)
        f.close()
    return


def save_report(data, file):
    def getkeys(row):
        result = []
        for key in row:
            result.append(key)
        return result

    def getusernames() -> []:
        result = []
        for row in data:
            if row['User'].strip() > '':
                if row['User'] not in result:
                    result.append(row['User'])
        return result

    users = getusernames()
    for user in users:
        # fill user_data with all rows for this user
        user_data = []
        for row in data:
            if row['User'] == user:
                user_data.append(row)
        # save user_data to file

        userfile = file + '-' + user + '.csv'

        report_title = get_report_title(user)
        with open(userfile, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['Report_Title'], delimiter='\t', quotechar='"',
                               quoting=csv.QUOTE_NONNUMERIC)
            w.writerow({'Report_Title': report_title})
            f.close()

        data_without_user = remove_column(user_data, 'User')
        fieldnames = []
        for row in data_without_user:
            fieldnames = getkeys(row)
            break

        with open(userfile, 'a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            w.writeheader()
            w.writerows(data_without_user)
            f.close()

    return


def save_report_html(data, file):
    def getkeys(row):
        result = []
        for key in row:
            result.append(key)
        return result

    def getusernames(data) -> []:
        result = []
        for row in data:
            if row['User'].strip() > '':
                if row['User'] not in result:
                    result.append(row['User'])
        return result

    def generate_css() -> str:
        x = '''
        <style>
            html {
                max-width: 70ch;
                padding: 3em 1em;
                margin: auto;
                line-height: 1.75;
                font-size: 1.25em;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }
            
            tr:nth-child(even) {
                background-color: #bbb;
            }

            /* ref: https://www.w3schools.com/css/css_tooltip.asp */            
            /* Tooltip container */
            .tooltip {
              position: relative;
              display: inline-block;
              border-bottom: 1px dotted black; /* If you want dots under the hoverable text */
            }
            
            /* Tooltip text */
            .tooltip .tooltiptext {
              visibility: hidden;
              width: 360px;
              background-color: lightpink;
              color: #000;
              text-align: left;
              padding: 2px 0;
              border-radius: 2px;
             
              /* Position the tooltip text - see examples below! */
              position: absolute;
              z-index: 1;
            }
            
            /* Show the tooltip text when you mouse over the tooltip container */
            .tooltip:hover .tooltiptext {
              visibility: visible;
            }            
        </style>
        '''
        return x

    # generate html buttons for top10 top20 top999
    def generate_buttons() -> str:
        x = '''
            <button onclick="show_top(10)">Top 10</button>
            <button onclick="show_top(20)">Top 20</button>
            <button onclick="show_top(9999)">All</button>
            <script>
            function show_top(n) {
              n = parseInt(n);
              var i;\n
              var rank;\n
              var x = document.getElementsByClassName("item");\n
              for (i = 0; i < x.length; i++) {\n
                rank = parseInt(x[i].getAttribute("data-rank"));\n
                if (rank <= n) {\n
                  // x[i].style.display = "block";\n
                  x[i].style.display = "";
                } else {\n
                  x[i].style.display = "none";\n
                }\n
              }\n
            }\n
            
            function count_mouseover() {\n
                let msg = "Count is defined as the number of times the URL was visited during the times listed";\n
                alert(msg);\n
            }\n
            </script>\n
        '''
        return x

    # generate html header
    def generate_header(rpt_title) -> str:
        x = f'''
            <!DOCTYPE html>\n
            <html>\n
            <head>\n
            <title>{rpt_title}</title>\n
            {generate_css()}
            </head>\n
            <body>\n
            '''
        return x

    full_data = copy.deepcopy(data)
    users = getusernames(data)
    for user in users:
        data = copy.deepcopy(full_data)
        # fill user_data with all rows for this user
        user_data = []
        for row in data:
            if row['User'] == user:
                user_data.append(row)
        # save user_data to file

        userfile = file + '-' + user + '.html'

        report_title = get_report_title(user)
        with open(userfile, 'w', newline='') as f:
            # generate standard html header
            f.write(generate_header(report_title))
            txt = f'<h1>{report_title}</h1>\n'
            f.write(txt)
            txt = generate_buttons()
            f.write(txt)
            f.close()

        data_without_user = remove_column(user_data, 'User')
        fieldnames = []
        for row in data_without_user:
            fieldnames = getkeys(row)
            break

        with open(userfile, 'a', newline='') as f:
            # generate table header
            txt = '<table>\n<thead>\n'
            f.write(txt)
            txt = '<tr>\n'
            f.write(txt)
            for fieldname in fieldnames:
                if fieldname == 'Count':
                    txt = f'<th class="tooltip">{fieldname}'
                    txt += '<span class="tooltiptext">'
                    txt += 'Count is defined as the number of times the URL was visited during the date range listed'
                    txt += '</span>'
                    txt += '</th>'
                else:
                    txt = f'<th>{fieldname}</th>\n'
                f.write(txt)
            txt = '</tr>\n'
            f.write(txt)
            txt = '</thead>\n'
            f.write(txt)

            rank = 0
            txt = '<tbody id="datatable">\n'
            f.write(txt)

            # generate table rows
            for row in data_without_user:
                rank += 1
                txt = f'<tr class="item" data-rank={rank}>'
                for fieldname in fieldnames:
                    txt += f'<td>{row[fieldname]}</td>'
                txt += '</tr>\n'
                f.write(txt)

            txt = '</tbody>\n'
            f.write(txt)
            txt = '</table>\n'
            f.write(txt)
            f.close()

        with open(userfile, 'a', newline='') as f:
            # generate standard html footer
            html_footer = '</body>\n</html>\n'
            f.write(html_footer)
            f.close()

    return


# extract domain from URL
def extract_domain(url: str) -> str:
    p = url.find('://', 1)
    if p > 0:
        url = url[p + 3:]
    p = url.find('/', 1)
    if p > 0:
        url = url[:p]

    # if last three characters are .org or .com or .net, then only include the last two parts
    if url[-4:] == '.org' or url[-4:] == '.com' or url[-4:] == '.net':
        p = url.rfind(".", 1, url.rfind('.'))
        if p > 0:
            url = url[p + 1:]

    return url


# create list of users from data
def get_users(data) -> []:
    users = []
    for row in data:
        if row['User_Profile'] not in users:
            users.append(row['User_Profile'])
    return users


# create list of domains from data
def get_domains(data) -> []:
    domains = []
    for row in data:
        if row['domain'] not in domains:
            domains.append(row['domain'])
    return domains


# create pivot table from data by user and domain
def pivot_by_user_domain(data) -> []:
    users = get_users(data)
    domains = get_domains(data)
    result = []
    for user in users:
        for domain in domains:
            onerec = {}
            onerec['User'] = user
            onerec['Domain'] = domain
            onerec['Count'] = 0
            for row in data:
                if row['User_Profile'] == user and row['domain'] == domain:
                    onerec['Count'] += 1
            result.append(onerec)

    # sort by user, then descending count
    result.sort(key=lambda x: (x['User'], -x['Count']))
    return result


# get minimum date from data
def get_min_date(data) -> str:
    min_date = '9999-12-31'
    for row in data:
        # convert date time string to date
        dateval = extract_date(row['Visit_Time'])
        dt = datetime.strptime(dateval, '%m/%d/%Y')
        if dt < datetime.strptime(min_date, '%Y-%m-%d'):
            min_date = dt.strftime('%Y-%m-%d')
    return min_date


# get maximum date from data
def get_max_date(data) -> str:
    max_date = '0001-01-01'
    for row in data:
        dateval = extract_date(row['Visit_Time'])
        dt = datetime.strptime(dateval, '%m/%d/%Y')
        if dt > datetime.strptime(max_date, '%Y-%m-%d'):
            max_date = dt.strftime('%Y-%m-%d')
    return max_date


# generate report title with date range
def get_report_title(username:str = None) -> str:
    min_date = get_min_date(data)
    max_date = get_max_date(data)
    if username is None:
        return f'Report for - {min_date} to {max_date}'
    else:
        return f'Report for {username} - {min_date} to {max_date}'
#    return 'Report for ' + os.path.basename(inputfile) + '/' + username + ', between ' + min_date + ' and ' + max_date


if __name__ == "__main__":
    getargs(sys.argv[0:])

    # # display inputfile, outputfile, and reportfile
    # print('inputfile: ' + inputfile)
    # print('outputfile: ' + outputfile)
    # print('reportfile: ' + reportfile)

    data = load_csv(inputfile)
    data = remove_non_data_rows(data)
    data = remove_column(data, 'URL_Length')
    data = remove_column(data, 'Typed_Count')
    data = remove_column(data, 'History_File')
    data = remove_column(data, 'Record_ID')
    data = remove_column(data, 'Visit_Count')
    data = remove_column(data, 'Visit_Type')
    data = remove_column(data, 'Browser_Profile')
    data = add_mdy_columns(data)
    data = add_hm_columns(data)
    save_csv(data, outputfile)
    save_html(data, outputfile)
    # sdata = pivot_by_user_domain(data)
    # save_report(sdata, reportfile)
    sdata = pivot_by_user_domain(data)
    save_report_html(sdata, reportfile)
