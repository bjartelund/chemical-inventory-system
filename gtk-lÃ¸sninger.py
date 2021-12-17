#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygtk,gtk,gtk.glade
import sys,csv,os
import copy
tabeller="losninger","stoffer"
try:
	import pgdb
	con = pgdb.connect(host="localhost",user="web_user",password="norstruct",database="kjemikalier")
except ImportError:
	from pysqlite2 import dbapi2 as sqlite
	con = sqlite.connect("losninger.db")
def getcursor():
	return con.cursor()

def None2False(variabel):
	if not variabel or variabel == '':
		return False
	else:
		return variabel
def dbtype2pythontype(column):
	"Tar typene fra cursor.description(Postgresql sine typer) og returnerer python-typer"
	if column[1] in ('varchar','char','date'):
		return column[0],str
	elif column[1] in "int4":
		return column[0],int
	elif column[1] in "float8":
		return column[0],float
	#Vi bryr oss ikke om andre typer
def quotestrings(string):

	if string.isdigit():
		return string
	try:
		float(string)
		return string
	except ValueError:
		return "'%s'" % string


class eksporter:
	def __init__(self,*args):
		gladefile="gtk-løsninger.glade"
		self.windowname="eksporter_window"
		self.wTree = gtk.glade.XML(gladefile,self.windowname)
		dic = {"on_eksporter":self.eksporter,
		"on_toggle_change":self.change_view}
		self.wTree.signal_autoconnect(dic)
		self.change_view()
		return
	def eksporter(self,*args):
		cursor = getcursor()
		if self.wTree.get_widget("Alle").get_active():
			cursor.execute("SELECT %s FROM %s" % (",".join(app.tabeller[app.tabell]),app.tabell))
		else:
			start = int(self.wTree.get_widget("start").get_text())
			slutt = int(self.wTree.get_widget("slutt").get_text())
			cursor.execute("SELECT %s FROM %s where id >= %i and id <= %i" % (",".join(app.tabeller[app.tabell]),app.tabell,start,slutt))
			
		dialog = gtk.FileChooserDialog("Eksporter", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_current_name("eksporterte.csv")	
		respons=dialog.run()
		if respons == gtk.RESPONSE_OK:
			data = csv.writer(open(dialog.get_filename(),"w"))
			data.writerow(app.tabeller[app.tabell])
			data.writerows(cursor.fetchall())
		dialog.destroy()
		self.wTree.get_widget("eksporter_window").destroy()
	def change_view(self,*args):
		if self.wTree.get_widget("start").state == 4:
			self.wTree.get_widget("start").set_sensitive(True)
			self.wTree.get_widget("slutt").set_sensitive(True)
		else:
			self.wTree.get_widget("start").set_sensitive(False)
			self.wTree.get_widget("slutt").set_sensitive(False)
			
		
class skjul_item:
	def __init__(self,*args):
		gladefile="gtk-løsninger.glade"
		self.windowname="skjul_oppføring"
		self.wTree = gtk.glade.XML(gladefile,self.windowname)
		dic = {	"on_Skjul_clicked":self.skjul}
		self.wTree.signal_autoconnect(dic)
		return
	def skjul(self,*args):
		cursor = getcursor()
		query = "UPDATE %s SET hidden = TRUE where id = %i" % (app.tabell,int(self.wTree.get_widget("id").get_text()))
		cursor.execute(query)
		con.commit()
		self.wTree.get_widget("skjul_oppføring").destroy()
class new_window:
	def __init__(self,*args):
		gladefile="gtk-løsninger.glade"
		self.windowname="ny"
		self.wTree = gtk.glade.XML(gladefile,self.windowname)
		dic = {"on_tabeller_changed":self.change_table,"ny":self.insert}
		self.wTree.signal_autoconnect(dic)
		entries_model =gtk.ListStore(str)
		for tabell in app.tabeller.keys():
			entries_model.append((tabell,))
		cell = gtk.CellRendererText()
		self.wTree.get_widget("tabeller").set_model(entries_model)
		self.wTree.get_widget("tabeller").set_text_column(0)
		self.wTree.get_widget("tabeller").pack_start(cell, True)
		self.wTree.get_widget("tabeller").add_attribute(cell, "text",1)
		self.tooltips = {"Navn":"Navn på løsning/stoff, evt. formel","Type":"Salt,Buffer,PEG,Ymse e.l","Molaritet":"Molaritet i tall, 5 for 5M","Prosent":"Prosenten i tall, oppgi hvis w/v under kommentarer. Skriv 50 for 50%","pH":"pH på løsningen der det gjelder, punktum som desimaltegn: 7.5","Dato":"Når løsningen/stoffet ble kjøpt/lagd. f.eks. 2005-08-23","Tilvirker":"Hvem lagde løsningen?","id":"Hva slags nummer skal løsningen ha i databasen, nyttig for redigering","Kommentarer":"Informasjon om stoffet/løsningen"}
		return
	def change_table(self,*args):
		#Skifter tabell
		self.entries = []
		#Fjerner alle barna til hbox entries og entries_labels
		for entry in self.wTree.get_widget("entries").get_children() + self.wTree.get_widget("entries_labels").get_children():
			entry.destroy()
		self.model = self.wTree.get_widget("tabeller").get_model()
		self.active = self.wTree.get_widget("tabeller").get_active()
		self.entries = app.tabeller[self.model[self.active][0]] #Henter kolonnenavn fra valgt tabell
		for entry in self.entries: #Itererer over kolonnenavnene og legger til labels og entries etter de navnene.
			entrybox = gtk.Entry()
			label = gtk.Label(entry)
			self.wTree.get_widget("entries").add(entrybox)
			self.wTree.get_widget("entries_labels").add(label)
			entrybox.show()
			label.show()
		for entry in zip(self.wTree.get_widget("entries").get_children(),self.wTree.get_widget("entries_labels").get_children()): #Tooltips om hver enkel entry, skal brukes til å vise hvilket format verdiene skal være i
			tooltip = gtk.Tooltips()
			tooltip.set_tip(entry[0],self.tooltips[entry[1].get_text()])
	def insert(self,*args):
		verdier = map(None2False,[x.get_text() for x in self.wTree.get_widget("entries").get_children()])
#		for entry in zip(app.tabeller[app.tabell],verdier):
		
		kolonner = copy.copy(app.tabeller[self.model[self.active][0]]) # Lager en kopi av kolonnene, ellers blir de slettet senere.
		if False in verdier: #Vi vil gjerne fjerne alle felt som ikke er fylt inn.
			count = 0
			for index in range(0,verdier.count(False)):
				index = verdier.index(False)
				verdier.pop(index),kolonner.pop(index)
		sqlquery= "INSERT INTO %s (%s) VALUES(%s)" % (self.model[self.active][0],",".join(kolonner),",".join(map(quotestrings,verdier)))
		cursor = getcursor()
		cursor.execute(sqlquery)
		con.commit()
		self.wTree.get_widget("ny").destroy()
class mainwindow:
	def __init__(self):
		gladefile="gtk-løsninger.glade"
		self.windowname="main"
		self.wTree = gtk.glade.XML(gladefile,self.windowname)
		dic = {"on_avslutt1_activate": self.avslutt, 
		"on_window1_destroy_event": self.avslutt, 
		"on_vis_tomme1_toggled": self.toggle_view_tomme,
		"on_vis_kun_nye1_toggled": self.toggle_view_kun_nye,
		"on_editing_done": self.search,
		"on_tabeller_row_activated":self.update_listview,
		"ny":new_window,
		"on_skjul_activate":skjul_item,
		"on_importer":self.importer,
		"on_eksporter":eksporter}
		self.wTree.signal_autoconnect(dic)
		self.listview = self.wTree.get_widget("treeview1")
		cursor=getcursor()
		self.tabeller,self.kolonnetyper,self.listmodels={},{},{} #Alle er dictionaries
		for tabell in tabeller:
			cursor.execute("SELECT * FROM %s LIMIT 1" % tabell) #Trenger bare ett resultat
			navn,type=[],[]
			for description in cursor.description:
				navnogtype = dbtype2pythontype(description)
				if navnogtype:
					navn.append(navnogtype[0]),type.append(navnogtype[1])
			self.tabeller[tabell],self.kolonnetyper[tabell] = navn,type
			self.listmodels[tabell] = gtk.ListStore(*self.kolonnetyper[tabell])
		self.kolonnetyper = {"losninger":[str,str,float,int,float,str,str,int,str],"stoffer":[str,str,str,int,int,str]}
		#self.listmodel = gtk.ListStore(str,str,float,int,float,str,str,int,str)
		#self.listmodels = {"losninger":gtk.ListStore(str,str,float,int,float,str,str,int,str),
		#"stoffer":gtk.ListStore(str,str,str,int,int,str)}
		self.entrymodels={}
		self.tabell_listview = self.wTree.get_widget("tabeller")
		self.tabell_listmodel = gtk.ListStore(str)
		self.tabell_listview.set_model(self.tabell_listmodel)
		self.rendrer = gtk.CellRendererText()
		self.tabell = "losninger"
		self.opt = "NOT hidden"
		self.columns= ["Navn","Type","Molaritet","Prosent","pH","Dato","Tilvirker","id","Kommentarer"]
		#self.tabeller= {"losninger":self.columns,"stoffer":["Navn","Type","Dato","id","hylle","Kommentarer"]}
		self.tabell_listview.append_column(gtk.TreeViewColumn("Tabell",self.rendrer,text=0))
		for tabell in self.tabeller.keys():
			self.tabell_listmodel.append((tabell,))
		self.wTree.get_widget("tabeller").set_cursor(1)
		self.update_listview()
		cursor.execute("SELECT %s from %s WHERE NOT hidden" % (",".join(self.tabeller[self.tabell]),self.tabell))
		self.listmodel=self.listmodels[self.tabell]
		for row in cursor.fetchall():
			self.listmodel.append(map(None2False,row))	
		return 
	def update_listview(self,*args):
		self.tabell= self.tabeller.keys()[self.wTree.get_widget("tabeller").get_cursor()[0][0]]
		self.listview.set_model(self.listmodels[self.tabell])
		id=0 # Denne inkrementeres. Plassering i tabell
		for column in self.listview.get_columns():
			self.listview.remove_column(column)
		for entry in self.wTree.get_widget("entries").get_children()+self.wTree.get_widget("entries_labels").get_children(): #Itererer over labels og entries, og sletter alle sammen, for så å lage nye
			entry.destroy()
		for column in self.tabeller[self.tabell]:
			kolonne = gtk.TreeViewColumn(column,self.rendrer,text=id)
			kolonne.set_sort_column_id(id)
			kolonne.set_resizable(True)
			self.listview.insert_column(kolonne,id)
			id+=1
			entrybox = gtk.Entry()
			label = gtk.Label(column)
			self.wTree.get_widget("entries").add(entrybox)
			self.wTree.get_widget("entries_labels").add(label)
			entrybox.show()
			label.show()

		
		for entry in zip(self.wTree.get_widget("entries").get_children(),self.wTree.get_widget("entries_labels").get_children()):
			entryname = str(entry[1].get_text())
			completion = gtk.EntryCompletion()
			
			cursor = getcursor()
			cursor.execute("SELECT distinct(%s) from %s" % (entryname,self.tabell))
			liststore = gtk.ListStore(str)
			for row in cursor.fetchall():
				liststore.append(row)
			completion.set_text_column(0)
			completion.set_model(liststore)
			self.entrymodels[entryname]=liststore
			completion.connect("match-selected",self.search)
			entry[0].connect("activate",self.search)
			entry[0].set_completion(completion)
		self.search(self)	
	def toggle_view_tomme(self,widget):
		"skal fjerne kravet om NOT HIDDEN for å også vise tomme løsninger"
		if self.wTree.get_widget("vis_tomme1").get_active():
			self.wTree.get_widget("vis_kun_nye1").set_sensitive(False)
			self.opt = " hidden "

		else:
			self.wTree.get_widget("vis_kun_nye1").set_sensitive(True)
			self.opt = " NOT hidden "
		self.search(self)	
	def toggle_view_kun_nye(self,widget):
		"Skal skifte tabell fra losninger til view'et dagens som viser dagens løsninger"
		if self.wTree.get_widget("vis_kun_nye1").get_active():
			self.wTree.get_widget("vis_tomme1").set_sensitive(False)
			self.opt =" lagtinn = current_date "
		else:
			self.wTree.get_widget("vis_tomme1").set_sensitive(True)
			self.opt =" NOT hidden "
		self.search(self)	
	def search(self,widget,variabel1=None,variabel2=None): 
		"Henter data fra tekstfeltene, og søker på disse i databasen"
		cursor = getcursor()
		query = "select %s from %s WHERE " % (",".join(self.tabeller[self.tabell]),self.tabell)
		kolonner,verdier= [x.get_text() for x in self.wTree.get_widget("entries_labels").get_children()],[x.get_text() for x in self.wTree.get_widget("entries").get_children()]
		for kolonne in kolonner:
			if verdier[kolonner.index(kolonne)] and kolonne in ("navn","type","dato","tilvirker","kommentarer"): #For strings.
				query += " %s ilike '%%%s%%' AND " % (kolonne,verdier[kolonner.index(kolonne)])
			elif verdier[kolonner.index(kolonne)] and kolonne in ("molaritet","ph"): #For floats
				query += "%s=%f AND " % (kolonne,float(verdier[kolonner.index(kolonne)]))
			elif verdier[kolonner.index(kolonne)] and kolonne in ("prosent","id"): #For Integers
				query += "%s=%i AND " % (kolonne,int(verdier[kolonner.index(kolonne)]))

		self.listmodels[self.tabell].clear()
		query += self.opt
		cursor.execute(query)
		for row in cursor.fetchall():
			self.listmodels[self.tabell].append(map(None2False,row))
	def importer(self,*args): #Lager en filechooser dialog, og importerer den valgte CSV-fila i databasen"
		dialog = gtk.FileChooserDialog("Importer", None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		filter = gtk.FileFilter()
		filter.set_name("CSV-filer")
		filter.add_pattern("*.csv")
		dialog.add_filter(filter)
		filter = gtk.FileFilter()
		filter.set_name("Alle filer")
		filter.add_pattern("*")
		dialog.add_filter(filter)
		respons=dialog.run()
		if respons == gtk.RESPONSE_OK:
			if os.path.exists(dialog.get_filename()): #Sjekker om fila eksisterer før vi gjør noe mer
				data = csv.reader(open(dialog.get_filename())) #leser inn csv-fila som ble importert
				self.kolonner = data.next() #Laster inn den første linja i csv-fila for å hente ut kolonnenavn
				cur = getcursor() # cursor til databasen
				for verdier in data:
					kolonner= copy.copy(self.kolonner)
					while "" in verdier: #Fjerner blanke felt fra csv-fila
						print kolonner
						print verdier
						kolonner.pop(verdier.index("")),verdier.pop(verdier.index("")) 
					verdier=map(quotestrings,verdier) # quoter strings, returnerer int for integers og returnerer float uten quotes.		
					cur.execute("DELETE FROM %s where id = %i" % (self.tabell,int(verdier[kolonner.index("id")]))) #Fjerner alle postene fra databasen som også er i csv-fila i mangel på en REPLACE-funksjon i postgresql
					cur.execute("INSERT INTO %s(%s) VALUES (%s) " % (self.tabell,",".join(kolonner),",".join(verdier))) #importerer alle postene i csv-fila
				con.commit() #Utfører endringene i databasen
		dialog.destroy()

		
	def avslutt(self,widget,event=None):
		sys.exit(2)
app=mainwindow()
gtk.main()
