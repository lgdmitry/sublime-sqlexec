import sublime, sublime_plugin, tempfile, os, subprocess, re #, asyncio
from sublime import Region

connection = None
history = ['']

class Connection:
    def __init__(self, options):
        self.settings = sublime.load_settings(options.type + ".sqlexec").get('sql_exec')
        self.command  = sublime.load_settings("SQLExec.sublime-settings").get('sql_exec.commands')[options.type]
        self.options  = options
        self.isOptions = 1;
        outputfile = sublime.load_settings("SQLExec.sublime-settings").get('sql_exec.outputfile')

        if outputfile.strip():
            self.settings['outputfile'].append(outputfile)
            self.outputfile = self.settings['outputfile']
        else:
            self.outputfile = []

    def _buildCommand(self, options):
        return self.command + ' ' + ' '.join(options) + ' ' + self.settings['args'].format(options=self.options)

    def _getCommand(self, options, queries, header = ''):
        command  = self._buildCommand(options)
        self.tmp = tempfile.NamedTemporaryFile(mode = 'w', delete = False, suffix='.sql')
        for query in self.settings['before']:
            self.tmp.write(query + "\n")
        for query in queries:
            self.tmp.write(query)
        self.tmp.close()

        cmd = '%s "%s"' % (command, self.tmp.name)
        print(cmd)
        return Command(cmd)

    def setOptions(self):
        self.isOptions = ~self.isOptions

    def setDatabaes(self, index):
        self.options.database = self.tempArray[index]

    def execute(self, queries):
        if self.isOptions == 1:
            options = list(self.settings['options']) + self.outputfile
        else:
            options = list(self.outputfile)
        command = self._getCommand(options, queries)

        command.run()
        os.unlink(self.tmp.name)

    def showDatabases(self):
        query = self.settings['queries']['show databases']['query']
        command = self._getCommand(self.settings['queries']['show databases']['options'], query)

        # command.show()
        db = []
        for result in command.run().splitlines():
            try:
                db.append(result.split('|')[0].strip())
            except IndexError:
                pass
        os.unlink(self.tmp.name)

        self.tempArray = db[2:len(db)-2]
        return self.tempArray

    def desc(self):
        query = self.settings['queries']['desc']['query']
        command = self._getCommand(self.settings['queries']['desc']['options'], query)

        # command.show()
        tables = []
        for result in command.run().splitlines():
            try:
                tables.append(result.split('|')[0].strip())
            except IndexError:
                pass

        os.unlink(self.tmp.name)

        self.tempArray = tables[2:len(tables)-2]
        return self.tempArray
        # return tables[2:len(tables)-2] #eliminace zahlavi, zapati

    def selectProc(self):
        query = self.settings['queries']['select proc']['query']
        command = self._getCommand(self.settings['queries']['select proc']['options'], query)

        # command.show()
        tables = []
        for result in command.run().splitlines():
            try:
                tables.append(result.split('|')[0].strip())
            except IndexError:
                pass

        os.unlink(self.tmp.name)

        return tables[2:len(tables)-2] #eliminace zahlavi, zapati

    def selectTable(self):
        query = self.settings['queries']['select table']['query']
        print(query)
        command = self._getCommand(self.settings['queries']['select table']['options'], query)
        # command.show()
        tables = []
        for result in command.run().splitlines():
            try:
                tables.append(result.split('|')[0].strip())
            except IndexError:
                pass

        os.unlink(self.tmp.name)

        return tables[2:len(tables)-2] #eliminace zahlavi, zapati

    def descTable(self, tableName):
        query = self.settings['queries']['desc table']['query'] % tableName
        if self.isOptions == 1:
            options = list(self.settings['queries']['desc table']['options']) + self.outputfile
        else:
            options = list(self.outputfile)

        command = self._getCommand(options, query)
        command.show()

        os.unlink(self.tmp.name)

    def showTableRecords(self, tableName):
        query = self.settings['queries']['show records']['query'] % tableName
        options = list(self.settings['queries']['show records']['options']) + self.outputfile
        command = self._getCommand(options, query)
        command.show()

        os.unlink(self.tmp.name)

    def showProcCode(self, objName):
        query = self.settings['queries']['show code']['query'] % objName[0]
        options = list(self.settings['queries']['show code']['options']) + self.outputfile
        command = self._getCommand(options, query)
        command.show()

        os.unlink(self.tmp.name)

class Command:
    def __init__(self, text):
        self.text = text

    def _display(self, panelName, text):
        if not sublime.load_settings("SQLExec.sublime-settings").get('show_result_on_window'):
            panel = sublime.active_window().create_output_panel(panelName)
            sublime.active_window().run_command("show_panel", {"panel": "output." + panelName})
        else:
            panel = sublime.active_window().new_file()

        panel.set_read_only(False)
        panel.set_syntax_file('Packages/SQL/SQL.tmLanguage')
        panel.run_command('append', {'characters': text})
        panel.set_read_only(True)

    def _result(self, text):
        self._display('SQLExec', text)

    def _errors(self, text):
        self._display('SQLExec.errors', text)

    def run(self):
        sublime.status_message(' SQLExec: running SQL command')
        results, errors = subprocess.Popen(self.text, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True).communicate()

        if not results and errors:
            self._errors(errors.decode('utf-8', 'replace').replace('\r', ''))

        temps = results.decode('utf-8', 'replace').replace('\r', '')
        return temps

    def run2(self):
        sublime.status_message(' SQLExec: running SQL command')
        p = subprocess.Popen(self.text, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True).communicate()

    def show(self):
        results = self.run()

        if results:
            self._result(results)

class Selection:
    def __init__(self, view):
        self.view = view
    def getQueries(self):
        text = []
        for region in self.view.sel():
            if region.empty():
                text.append(self.view.substr(Region(0, self.view.size())))
            else:
                text.append(self.view.substr(region))
        return text

class Options:
    def __init__(self, name):
        self.name     = name
        connections   = sublime.load_settings("SQLExec.sublime-settings").get('connections')
        self.type     = connections[self.name]['type']
        self.host     = connections[self.name]['host']
        self.port     = connections[self.name]['port']
        self.username = connections[self.name]['username']
        self.password = connections[self.name]['password']
        self.database = connections[self.name]['database']
        output = connections[self.name]['output']
        if output.strip():
            self.output = '-o ' + output
        else:
            self.output = ''

        if 'service' in connections[self.name]:
            self.service  = connections[self.name]['service']

    def __str__(self):
        return self.name

    @staticmethod
    def list():
        names = []
        connections = sublime.load_settings("SQLExec.sublime-settings").get('connections')
        for connection in connections:
            names.append(connection)
        names.sort()
        return names

def sqlChangeConnection(index):
    global connection
    names = Options.list()
    options = Options(names[index])
    connection = Connection(options)
    sublime.status_message(' SQLExec: switched to connection %s' % names[index])

def showTableRecords(index):
    global connection
    if index > -1:
        if connection != None:
            print('command: showTableRecords')
            tables = connection.selectTable()
            connection.showTableRecords(tables[index])
        else:
            sublime.error_message('No active connection')

def descTable(index):
    global connection
    if index > -1:
        if connection != None:
            # tables = connection.desc()
            # connection.descTable(tables[index])
            connection.descTable(connection.tempArray[index])
        else:
            sublime.error_message('No active connection')

def executeHistoryQuery(index):
    global history
    if index > -1:
        executeQuery(history[index])

def executeQuery(query):
    global connection
    global history
    history.append(query)
    history = list(set(history))
    if connection != None:
        connection.execute(query)

def setDatabaes(database):
    global connection
    if connection != None:
        connection.setDatabaes(database)
    else:
        sublime.error_message('No active connection')

class sqlHistory(sublime_plugin.WindowCommand):
    global history
    def run(self):
        sublime.active_window().show_quick_panel(history, executeHistoryQuery)

class sqlDesc(sublime_plugin.WindowCommand):
    def run(self):
        global connection
        if connection != None:
            tables = connection.desc()
            sublime.active_window().show_quick_panel(tables, descTable)
        else:
            sublime.error_message('No active connection')

class sqlShowRecords(sublime_plugin.WindowCommand):
    def run(self):
        global connection
        if connection != None:
            # tables = connection.showTableRecords()
            tables = connection.selectTable()
            sublime.active_window().show_quick_panel(tables, showTableRecords)
        else:
            sublime.error_message('No active connection')

class sqlQuery(sublime_plugin.WindowCommand):
    def run(self):
        global connection
        global history
        if connection != None:
            sublime.active_window().show_input_panel('Enter query', history[-1], executeQuery, None, None)
        else:
            sublime.error_message('No active connection')

class sqlExecute(sublime_plugin.WindowCommand):
    def run(self):
        global connection
        if connection != None:
            selection = Selection(self.window.active_view())
            connection.execute(selection.getQueries())
        else:
            sublime.error_message('No active connection')

class sqlListConnection(sublime_plugin.WindowCommand):
    def run(self):
        sublime.active_window().show_quick_panel(Options.list(), sqlChangeConnection)

class sqlHelpText(sublime_plugin.WindowCommand):
    def run(self):
        global connection
        if connection != None:
            selection = Selection(self.window.active_view())
            connection.showProcCode(selection.getQueries())
        else:
            sublime.error_message('No active connection')

class sqlHelp(sublime_plugin.WindowCommand):
    def run(self):
        global connection
        if connection != None:
            selection = Selection(self.window.active_view())
            connection.descTable(selection.getQueries()[0])
        else:
            sublime.error_message('No active connection')

class sqlSetOptions(sublime_plugin.WindowCommand):
    def run(self):
        global connection
        if connection != None:
            selection = Selection(self.window.active_view())
            connection.setOptions()
        else:
            sublime.error_message('No active connection')

class sqlShowDatabases(sublime_plugin.WindowCommand):
    def run(self):
        global connection
        if connection != None:
            db = connection.showDatabases()
            sublime.active_window().show_quick_panel(db, setDatabaes)
        else:
            sublime.error_message('No active connection')
