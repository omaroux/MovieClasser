import os
import datetime
import re
from collections import namedtuple
import tkinter as tk
from tkinter import ttk, filedialog
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from tkinter import messagebox
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from tkinter import filedialog
import pickle

class MovieTranslator:
    def __init__(self):
        self.movies = []
        self.Movie = namedtuple('Movie', ['name', 'rcv_date', 'del_date', 'lines', 'length', 'earnings', 'days_to_finish'])

    def add_movie(self, srt_file, rcv_date_str, del_date_str, earnings=None):
        rcv_date = datetime.datetime.strptime(rcv_date_str, "%Y-%m-%d")
        del_date = datetime.datetime.strptime(del_date_str, "%Y-%m-%d")
        name, lines = self.parse_srt(srt_file)
        length = self.get_movie_length(lines)
        if earnings is None:
            earnings = self.calculate_earnings(lines)
        else:
            earnings = float(earnings)
        days_to_finish = (del_date - rcv_date).days
        movie = self.Movie(name, rcv_date, del_date, lines, length, earnings, days_to_finish)
        self.movies.append(movie)
        self.movies.sort(key=lambda m: m.rcv_date)

    def parse_srt(self, srt_file):
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = re.findall(r'\d+\n\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+\n(.+)', content, re.MULTILINE)
            name = os.path.basename(srt_file).replace('.srt', '')
        return name, len(lines)

    def get_movie_length(self, lines):
        if lines < 700: return 'normally long'
        elif 700 <= lines < 1400: return 'average long'
        else: return 'very long'

    def calculate_earnings(self, lines):
        return lines * 56
    
class MovieTranslatorGUI:
    def __init__(self, translator):
        self.translator = translator
        self.root = tk.Tk()
        self.root.title('Movie Translator')
        self.movie_entries = []

        self.add_movie_button = tk.Button(self.root, text='Add Movie', command=self.add_movie)
        self.add_movie_button.grid(row=0, column=0, padx=5, pady=5)

        self.display_movies_button = tk.Button(self.root, text='Display Movies', command=self.display_movies)
        self.display_movies_button.grid(row=0, column=1, padx=5, pady=5)

        self.export_pdf_button = tk.Button(self.root, text='Export PDF', command=self.export_pdf)
        self.export_pdf_button.grid(row=0, column=2, padx=5, pady=5)

        self.edit_movie_button = tk.Button(self.root, text='Edit Movie', command=self.edit_movie)
        self.edit_movie_button.grid(row=0, column=3, padx=5, pady=5)
        self.save_project_button = tk.Button(self.root, text='Save Project', command=self.save_project)
        self.save_project_button.grid(row=0, column=4, padx=5, pady=5)

        self.load_project_button = tk.Button(self.root, text='Load Project', command=self.load_project)
        self.load_project_button.grid(row=0, column=5, padx=5, pady=5)

        self.movie_list = ttk.Treeview(self.root, columns=('Name', 'Receiving Date', 'Delivery Date', 'Lines', 'Length', 'Earnings', 'Days to Finish'), show='headings')
        for col in self.movie_list['columns']:
            self.movie_list.heading(col, text=col)
        self.movie_list.grid(row=1, column=0, columnspan=6, padx=5, pady=5)
        
    def save_project(self):
        project_file = filedialog.asksaveasfilename(defaultextension=".proj", filetypes=[("Project files", "*.proj")])

        if not project_file:
            return

        with open(project_file, "wb") as f:
            pickle.dump(self.translator.movies, f)

        messagebox.showinfo("Success", "Project saved successfully.")

    def load_project(self):
        project_file = filedialog.askopenfilename(filetypes=[("Project files", "*.proj"), ("All Files", "*.*")])

        if not project_file:
            return

        with open(project_file, "rb") as f:
            self.translator.movies = pickle.load(f)

        self.display_movies()

    def add_movie(self):
        movie_entry = MovieEntryWindow(self.root, self.translator, mode='add')
        self.movie_entries.append(movie_entry)


    def display_movies(self):
        for movie_item in self.movie_list.get_children():
            self.movie_list.delete(movie_item)
        
        for movie in self.translator.movies:
            self.movie_list.insert('', 'end', values=(movie.name, movie.rcv_date.strftime('%Y-%m-%d'), movie.del_date.strftime('%Y-%m-%d'), movie.lines, movie.length, f"${movie.earnings:.2f}", movie.days_to_finish))

    def edit_movie(self):
        selected_items = self.movie_list.selection()

        if not selected_items:
            messagebox.showerror("Error", "Please select a movie to edit.")
            return

        selected_item = selected_items[0]
        movie_index = self.movie_list.index(selected_item)
        
        movie_entry = MovieEntryWindow(self.root, self.translator, 'edit', movie_index)
        self.movie_entries.append(movie_entry)

    def export_pdf(self):
        if not self.translator.movies:
            messagebox.showerror("Error", "No movies to export.")
            return

        pdf_file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])

        if not pdf_file:
            return

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        data = [['Name', 'Receiving Date', 'Delivery Date', 'Lines', 'Length', 'Earnings', 'Days to Finish']]

        for movie in self.translator.movies:
            data.append([movie.name, movie.rcv_date.strftime('%Y-%m-%d'), movie.del_date.strftime('%Y-%m-%d'), movie.lines, movie.length, f"${movie.earnings:.2f}", movie.days_to_finish])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),

            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),

            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        doc.build([table])

        with open(pdf_file, "wb") as f:
            f.write(buffer.getvalue())
            buffer.close()

        messagebox.showinfo("Success", "PDF exported successfully.")
         
class MovieEntryWindow:
    def __init__(self, parent, translator, mode='add', movie_index=None):
        self.translator = translator
        self.mode = mode
        self.movie_index = movie_index
        self.top = tk.Toplevel(parent)
        if mode == 'add':
            self.top.title('Add Movie')
        elif mode == 'edit':
            self.top.title('Edit Movie')

        labels = ['SRT File:', 'Receiving Date:', 'Delivery Date:', 'Earnings:']
        self.entries = []
        for i, lbl in enumerate(labels):
            tk.Label(self.top, text=lbl).grid(row=i, column=0, padx=5, pady=5)
            if i == 0 and mode == 'add':
                self.browse_button = tk.Button(self.top, text='Browse', command=self.browse_srt)
                self.browse_button.grid(row=i, column=2, padx=5, pady=5)
            self.entries.append(tk.Entry(self.top))
            self.entries[-1].grid(row=i, column=1, padx=5, pady=5)

        if mode == 'edit':
            movie = self.translator.movies[movie_index]
            self.entries[0].insert(0, movie.name + '.srt')
            self.entries[1].insert(0, movie.rcv_date.strftime('%Y-%m-%d'))
            self.entries[2].insert(0, movie.del_date.strftime('%Y-%m-%d'))
            self.entries[3].insert(0, movie.earnings)
        self.submit_button = tk.Button(self.top, text='Submit', command=self.submit_movie)
        self.submit_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

    def browse_srt(self):
        srt_file = filedialog.askopenfilename(filetypes=[("SRT Files", "*.srt"), ("All Files", "*.*")])
        if srt_file:
            self.entries[0].delete(0, tk.END)
            self.entries[0].insert(0, srt_file)

    def submit_movie(self):
        srt_file = self.entries[0].get()
        rcv_date_str = self.entries[1].get()
        del_date_str = self.entries[2].get()
        earnings = self.entries[3].get()

        if not rcv_date_str or not del_date_str:
            messagebox.showerror("Error", "Please enter valid date values.")
            return

        if self.mode == 'add':
            self.translator.add_movie(srt_file, rcv_date_str, del_date_str, earnings)
        elif self.mode == 'edit':
            movie = self.translator.movies[self.movie_index]
            updated_movie = self.translator.Movie(movie.name, datetime.datetime.strptime(rcv_date_str, "%Y-%m-%d"), datetime.datetime.strptime(del_date_str, "%Y-%m-%d"), movie.lines, movie.length, float(earnings), (datetime.datetime.strptime(del_date_str, "%Y-%m-%d") - datetime.datetime.strptime(rcv_date_str, "%Y-%m-%d")).days)
            self.translator.movies[self.movie_index] = updated_movie

        self.top.destroy()

def print_pdf(translator, start_date=None, end_date=None):
    doc = SimpleDocTemplate("movie_translator_report.pdf", pagesize=letter)
    data = [['Name', 'Receiving Date', 'Delivery Date', 'Lines', 'Length', 'Earnings', 'Days to Finish']]
    for movie in translator.movies:
        if start_date and movie.rcv_date < start_date:
            continue
        if end_date and movie.rcv_date > end_date:
            continue
        data.append([movie.name, movie.rcv_date.strftime('%Y-%m-%d'), movie.del_date.strftime('%Y-%m-%d'), movie.lines, movie.length, f"${movie.earnings:.2f}", movie.days_to_finish])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    doc.build([table])

if __name__ == '__main__':
    movie_translator = MovieTranslator()
    gui = MovieTranslatorGUI(movie_translator)
    gui.root.mainloop()
