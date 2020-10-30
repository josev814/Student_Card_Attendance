import datetime
import os
import re
import time
from configparser import ConfigParser

import wx

attendance_file = 'attendance'
filename_with_class = False
filename_with_date = False
VERSION = 0.2
DEBUG = False
classes = []
class_student_files = {}
CONFIGFILE = 'scanner.config'
APPW = 500
APPH = 300


class TheClassPanel(wx.Panel):
    thisClass = None
    listClasses = None

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)

    def select_class(self):
        # display scan message
        st = wx.StaticText(self, label="Select Class", style=wx.ALIGN_LEFT)
        font = st.GetFont()
        font.PointSize += 10
        font = font.Bold()
        st.SetFont(font)

        # create a sizer to manage the layout of child widgets
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(st)
        vbox.Add(hbox1, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.listClasses = wx.ListBox(self, choices=classes, style=wx.LB_SINGLE|wx.LB_NEEDED_SB)
        hbox2.Add(self.listClasses)

        vbox.Add(hbox2, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))

        self.SetSizer(vbox)

    def on_list_select(self, *args):
        selection = self.listClasses.GetString(self.listClasses.GetSelection())
        if selection in classes:
            self.thisClass = selection
            if DEBUG:
                print(self.thisClass)

    def get_class(self):
        return self.thisClass


class ScanPanel(wx.Panel):
    """"
    A Frame that says to Scan ID Card
    """
    charCount = 0
    minCount = 5
    studentIds = []
    studentNames = {}
    default_label = 'Scan Your ID Card'
    start_datetime = str(datetime.datetime.now())
    classId = None
    st = None
    txt = None
    full_date = None

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.short_date = self.start_datetime[:10]
        self.filename = attendance_file
        if filename_with_date:
            self.filename = '{}_{}'.format(self.filename, self.short_date)

    def reset(self):
        self.studentIds = []
        self.studentNames = {}
        self.filename = attendance_file
        if filename_with_date:
            self.filename = '{}_{}'.format(self.filename, self.short_date)
        self.start_datetime = str(datetime.datetime.now())
        self.classId = None

    def load_students(self):
        self.GetParent().PushStatusText('Loading Class Students: {}'.format(self.classId))
        if DEBUG:
            print(class_student_files[self.classId])
        student_class_file = class_student_files[self.classId]
        if DEBUG:
            print(os.path.exists(student_class_file))
        if os.path.exists(student_class_file):
            with open(student_class_file, 'r') as scfh:
                scfh.readline()  # header row (call to skip it)
                row = scfh.readline()
                while row:
                    columns = row.split(',')
                    name = columns[0].replace('"', '').rstrip('\n')
                    student_id = columns[1].rstrip('\n')
                    self.studentNames[student_id] = name
                    row = scfh.readline()
                if DEBUG:
                    print(self.studentNames)
        self.load_already_logged_in()
        self.GetParent().PopStatusText()

    def load_already_logged_in(self):
        self.GetParent().PushStatusText('Loading Class Students Logged In: {}'.format(self.classId))
        if os.path.exists(self.filename + '.csv'):
            with open(self.filename + '.csv', 'r') as scfh:
                scfh.readline()  # header row (call to skip it)
                row = scfh.readline()
                while row:
                    columns = row.split(',')
                    student_id = columns[2]
                    if student_id not in self.studentIds:
                        self.studentIds.append(student_id)
                    row = scfh.readline()
        if DEBUG:
            print(self.studentIds)
        self.GetParent().PopStatusText()

    def scan_id_card(self):
        # display scan message
        self.st = wx.StaticText(
            self,
            label=self.default_label,
            style=wx.ALIGN_LEFT,
            size=wx.Size(self.GetParent().GetSize()[0] - 20, -1)
        )
        font = self.st.GetFont()
        font.PointSize += 10
        font = font.Bold()
        self.st.SetFont(font)

        # create a sizer to manage the layout of child widgets
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.st)
        vbox.Add(hbox1, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.txt = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        hbox2.Add(self.txt)

        vbox.Add(hbox2, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))
        self.txt.Bind(wx.EVT_KEY_UP, self.on_key_press)
        self.SetSizer(vbox)

    def on_key_press(self, event):
        input_len = len(self.txt.GetValue())
        if input_len > self.charCount or input_len < self.minCount:
            self.charCount = input_len
        else:
            student_id = self.txt.GetValue()[1:-1]
            if self.check_student_entry(student_id):
                if DEBUG:
                    print(student_id)
                status = "Already Logged In: {}".format(student_id)
                student_name = self.get_student_name(student_id)
                if student_name != "Unregistered":
                    if DEBUG:
                        print(student_name)
                    status = "Already Logged In: {}".format(student_name)
                if DEBUG:
                    print(status)
                self.GetParent().PushStatusText(status)
                self.st.SetLabel(status)
                time.sleep(2)
            else:
                status = "Saving Login: {}".format(student_id)
                student_name = self.get_student_name(student_id)
                if student_name != "Unregistered":
                    status = "Saving Login: {}".format(student_name)
                self.GetParent().PushStatusText(status)
                self.st.SetLabel(status)
                self.full_date = str(datetime.datetime.now())[:-7]
                self.save_entry(student_id, student_name)
                self.studentIds.append(student_id)
                time.sleep(2)
            self.txt.SetValue('')
            self.GetParent().PopStatusText()
            self.GetParent().PopStatusText()
            self.st.SetLabel(self.default_label)

    def get_student_name(self, student_id):
        student_name = 'Unregistered'
        if student_id in self.studentNames:
            student_name = self.studentNames[student_id]
        if DEBUG:
            print(student_name)
        return student_name

    def check_student_entry(self, student_id):
        status = "Checking Entry: " + student_id
        self.GetParent().PushStatusText(status)
        self.st.SetLabel(status)
        if student_id in self.studentIds:
            return True
        return False

    def save_entry(self, student_id, student_name):
        short_date = self.full_date[:10]
        with open('{}.csv'.format(self.filename), 'a') as afh:
            csv_line = '{},{},{},{},{}\n'.format(self.full_date, short_date, student_id, student_name, self.classId)
            afh.write(csv_line)

    def create_csv(self):
        with open('{}.csv'.format(self.filename), 'w') as afh:
            csvline = '{},{},{},{},{}\n'.format('Date Time', 'Date', 'Student ID', 'Student Name', 'Class')
            afh.write(csvline)

    def set_class(self, class_id):
        self.classId = class_id
        if filename_with_class:
            self.filename = '{}_{}'.format(self.classId, self.filename)
        if os.path.isfile(self.filename + '.csv') is False:
            self.create_csv()


class MyForm(wx.Frame):

    defaultStatus = 'Welcome to UNCP'

    def __init__(self):
        try:
            if os.path.exists(CONFIGFILE) is False:
                self.create_config_file()
            self.load_config_vars()
            wx.Frame.__init__(self, None, wx.ID_ANY, "UNCP Attendance Tracker {}".format(VERSION))
            self.SetSize(wx.Size(APPW, APPH))
            # create a menu bar
            self.make_menu_bar()

            # and a status bar
            self.CreateStatusBar()
            self.classId = None
            self.class_panel = TheClassPanel(self)
            self.class_panel.select_class()
            self.attendance_panel = ScanPanel(self)
            self.attendance_panel.scan_id_card()
            self.attendance_panel.Hide()

            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.sizer.Add(self.class_panel, 1, wx.EXPAND)
            self.sizer.Add(self.attendance_panel, 1, wx.EXPAND)
            self.SetSizer(self.sizer)

            self.class_panel.listClasses.Bind(wx.EVT_LISTBOX_DCLICK, self.on_switch_panels)
            self.SetStatusText(self.defaultStatus)
        except Exception as e:
            print(e)
            time.sleep(10)

    def on_switch_panels(self, event):
        if self.class_panel.IsShown():
            self.class_panel.on_list_select()
            self.classId = self.class_panel.get_class()
            self.attendance_panel.set_class(self.classId)
            if self.class_panel.thisClass is not None:
                self.SetTitle("UNCP Student Attendance {}".format(VERSION))
                self.class_panel.Hide()
                self.attendance_panel.load_students()
                self.attendance_panel.Show()
                self.attendance_panel.txt.SetFocus()
                self.SetStatusText('{}: {}'.format(self.defaultStatus, self.classId))
        else:
            self.SetTitle("UNCP Class Selection {}".format(VERSION))
            self.attendance_panel.reset()
            self.class_panel.Show()
            self.attendance_panel.Hide()
        self.Layout()

    def make_menu_bar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        file_menu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        """helloItem = file_menu.Append(-1, "&Hello...\tCtrl-H",
                                    "Help string shown in status bar for this menu item")
        file_menu.AppendSeparator()
        """
        change_class = file_menu.Append(-1, "&Change Class")
        file_menu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exit_item = file_menu.Append(wx.ID_EXIT)

        # Now a help menu for the about item
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(help_menu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menu_bar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        # self.Bind(wx.EVT_MENU, self.on_hello, helloItem)
        self.Bind(wx.EVT_MENU, self.on_change_class, change_class)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def on_change_class(self, event):
        """Switch Frame for changing classes"""
        self.SetTitle("UNCP Class Selection {}".format(VERSION))
        self.SetStatusText(self.defaultStatus)
        self.attendance_panel.reset()
        self.class_panel.Show()
        self.attendance_panel.Hide()
        self.Layout()

    def on_exit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def on_about(self, event):
        """Display an About Dialog"""
        wx.MessageBox("Written By Jose' Vargas\r\nWritten in Python 3.7\r\nPackages used:\r\nwxPython,ConfigParser",
                      'About {}'.format(self.Title),
                      wx.OK | wx.ICON_INFORMATION)

    def create_config_file(self):
        global DEBUG
        config = ConfigParser()
        config.add_section('default')
        config.set('default', 'debug', 'False')
        config.set('default', 'appw', '500')
        config.set('default', 'apph', '300')
        config.set('default', 'filename_with_class','True')
        config.set('default', 'filename_with_date', 'True')
        config.set('default', 'class_count', '1')
        config.add_section('class_1')
        config.set('class_1', 'id', 'SOC 1020')
        config.set('class_1', 'time', '9AM')
        config.set('class_1', 'name', 'Intro To Sociology')
        config.set('class_1', 'students_csv_file', 'Intro To Sociology SOC 1020 9AM_students.csv')
        with open(CONFIGFILE, 'w') as configfile:
            config.write(configfile)

    def load_config_vars(self):
        global DEBUG
        global APPW
        global APPH
        global classes
        global filename_with_date
        global filename_with_class
        config = ConfigParser()
        config.read(CONFIGFILE)
        if 'default' in config:
            if 'debug' in config['default'] and re.match(r'true', config['default']['debug'], re.IGNORECASE):
                DEBUG = True
            if 'appw' in config['default'] and re.match(r'([\d]+)', config['default']['appw']):
                APPW = int(re.findall(r'([\d]+)', config['default']['appw'])[0])
            if 'appw' in config['default'] and re.match(r'([\d]+)', config['default']['apph']):
                APPH = int(re.findall(r'([\d]+)', config['default']['apph'])[0])
            if 'filename_with_class' in config['default'] and re.match(r'true', config['default']['filename_with_class'], re.IGNORECASE):
                filename_with_class = True
            if 'filename_with_date' in config['default'] and re.match(r'true', config['default']['filename_with_date'], re.IGNORECASE):
                filename_with_date = True
            if 'class_count' in config['default'] and re.match(r'([\d]+)', config['default']['class_count']):
                class_count = int(re.findall(r'([\d]+)', config['default']['class_count'])[0])
            for i in range(1, class_count + 1):
                class_name = '{} {} {}'.format(
                        config['class_{}'.format(i)]['name'].replace('/', '-').replace(':', ' '),
                        config['class_{}'.format(i)]['id'],
                        config['class_{}'.format(i)]['time'].replace(':', '')
                    )
                classes.append(class_name)
                class_student_files[class_name] = '{}'.format(
                    config['class_{}'.format(i)]['students_csv_file']
                )
            if DEBUG:
                print(class_student_files)
        if DEBUG:
            print('default: {}\nclass_1: {}\n'.format(config['default'], config['class_1']))


if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App(False)
    frm = MyForm()
    # frm.scan_id_card()
    frm.Show()
    app.MainLoop()


