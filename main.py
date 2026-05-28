"""
Трекер расходов — Kivy приложение для Android
"""

import json
import os
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

# ──────────────────────────────────────────────
#  Цветовая палитра
# ──────────────────────────────────────────────
C = {
    "bg":       "#0F0F1A",
    "surface":  "#1A1A2E",
    "card":     "#16213E",
    "accent":   "#7C5CBF",
    "accent2":  "#5BC4A0",
    "danger":   "#E05C5C",
    "warn":     "#E0A85C",
    "text":     "#F0EEF8",
    "muted":    "#8B8AA0",
    "border":   "#2A2A45",
}

CATS = [
    ("🏠 Жильё",       "#7C5CBF"),
    ("🍕 Еда",         "#5BC4A0"),
    ("🚌 Транспорт",   "#E0A85C"),
    ("❤️ Здоровье",    "#E05C5C"),
    ("🎮 Развлечения", "#5C9EE0"),
    ("👗 Одежда",      "#E05C9E"),
    ("📚 Образование", "#5CE07C"),
    ("📦 Прочее",      "#8B8AA0"),
]
CAT_NAMES  = [c[0] for c in CATS]
CAT_COLORS = {c[0]: c[1] for c in CATS}

DATA_FILE = "budget_data.json"


# ──────────────────────────────────────────────
#  Хранилище данных
# ──────────────────────────────────────────────
class DataStore:
    def __init__(self):
        self.income   = 0.0
        self.currency = "₽"
        self.expenses = []   # [{name, amount, category, date}]
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.income   = d.get("income", 0.0)
                self.currency = d.get("currency", "₽")
                self.expenses = d.get("expenses", [])
            except Exception:
                pass

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "income":   self.income,
                "currency": self.currency,
                "expenses": self.expenses,
            }, f, ensure_ascii=False, indent=2)

    @property
    def total(self):
        return sum(e["amount"] for e in self.expenses)

    @property
    def balance(self):
        return self.income - self.total

    def add_expense(self, name, amount, category):
        self.expenses.append({
            "name":     name,
            "amount":   float(amount),
            "category": category,
            "date":     datetime.now().strftime("%d.%m.%Y"),
        })
        self.save()

    def remove_expense(self, index):
        self.expenses.pop(index)
        self.save()

    def fmt(self, value):
        sign = "-" if value < 0 else ""
        return f"{sign}{self.currency} {abs(value):,.0f}".replace(",", " ")

    def cat_totals(self):
        totals = {}
        for e in self.expenses:
            totals[e["category"]] = totals.get(e["category"], 0) + e["amount"]
        return sorted(totals.items(), key=lambda x: x[1], reverse=True)


store = DataStore()


# ──────────────────────────────────────────────
#  Вспомогательные виджеты
# ──────────────────────────────────────────────
def hex_c(h):
    return get_color_from_hex(h)


class RoundedBox(Widget):
    """Фоновая карточка с закруглёнными углами."""
    def __init__(self, color, radius=dp(14), **kw):
        super().__init__(**kw)
        self._color  = color
        self._radius = radius
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*hex_c(self._color))
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self._radius])


def card(color=None, radius=dp(14), **kw):
    c = color or C["card"]
    b = BoxLayout(**kw)
    with b.canvas.before:
        Color(*hex_c(c))
        b._rect = RoundedRectangle(pos=b.pos, size=b.size,
                                   radius=[radius])
    b.bind(pos=lambda o, v: setattr(o._rect, "pos", v),
           size=lambda o, v: setattr(o._rect, "size", v))
    return b


def lbl(text, size=dp(14), color=None, bold=False, halign="left", **kw):
    l = Label(
        text=text,
        font_size=size,
        color=hex_c(color or C["text"]),
        bold=bold,
        halign=halign,
        text_size=(None, None),
        **kw,
    )
    l.bind(size=lambda o, v: setattr(o, "text_size", (v[0], None)))
    return l


def btn(text, on_press=None, bg=None, fg=None, radius=dp(10), size_hint_x=1, **kw):
    b = Button(
        text=text,
        font_size=dp(14),
        color=hex_c(fg or C["text"]),
        background_normal="",
        background_color=hex_c(bg or C["accent"]),
        size_hint_x=size_hint_x,
        **kw,
    )
    if on_press:
        b.bind(on_press=on_press)
    return b


def sep():
    w = Widget(size_hint_y=None, height=dp(1))
    with w.canvas:
        Color(*hex_c(C["border"]))
        Rectangle(pos=w.pos, size=w.size)
    w.bind(pos=lambda o, v: setattr(o.canvas.children[-1], "pos", v),
           size=lambda o, v: setattr(o.canvas.children[-1], "size", v))
    return w


# ──────────────────────────────────────────────
#  Экран 1: Главный (сводка)
# ──────────────────────────────────────────────
class HomeScreen(Screen):
    def __init__(self, sm, **kw):
        super().__init__(name="home", **kw)
        self.sm = sm
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=dp(16), spacing=dp(12))
        with root.canvas.before:
            Color(*hex_c(C["bg"]))
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda o, v: setattr(o._bg, "pos", v),
                  size=lambda o, v: setattr(o._bg, "size", v))

        # Заголовок
        root.add_widget(lbl("💰 Мой бюджет", size=dp(22), bold=True,
                             halign="center",
                             size_hint_y=None, height=dp(40)))

        # Карточка дохода
        self.income_card = BoxLayout(orientation="vertical",
                                     size_hint_y=None, height=dp(90),
                                     padding=dp(14), spacing=dp(4))
        with self.income_card.canvas.before:
            Color(*hex_c(C["surface"]))
            self.income_card._rect = RoundedRectangle(
                pos=self.income_card.pos, size=self.income_card.size,
                radius=[dp(14)])
        self.income_card.bind(
            pos=lambda o, v: setattr(o._rect, "pos", v),
            size=lambda o, v: setattr(o._rect, "size", v))

        self.income_lbl  = lbl("", size=dp(26), bold=True, halign="center",
                                color=C["accent2"])
        self.balance_lbl = lbl("", size=dp(13), halign="center", color=C["muted"])
        self.income_card.add_widget(self.income_lbl)
        self.income_card.add_widget(self.balance_lbl)
        root.add_widget(self.income_card)

        # Три плашки: доход / расход / остаток
        row = GridLayout(cols=3, spacing=dp(8),
                         size_hint_y=None, height=dp(80))
        self.stat_income   = self._stat_card("Доход",   C["accent2"])
        self.stat_expenses = self._stat_card("Расходы", C["warn"])
        self.stat_balance  = self._stat_card("Остаток", C["accent"])
        for w in (self.stat_income, self.stat_expenses, self.stat_balance):
            row.add_widget(w)
        root.add_widget(row)

        # Список расходов по категориям
        root.add_widget(lbl("По категориям", size=dp(13),
                             color=C["muted"], size_hint_y=None, height=dp(20)))
        scroll = ScrollView(size_hint=(1, 1))
        self.cat_list = BoxLayout(orientation="vertical",
                                  spacing=dp(8), size_hint_y=None)
        self.cat_list.bind(minimum_height=self.cat_list.setter("height"))
        scroll.add_widget(self.cat_list)
        root.add_widget(scroll)

        # Кнопки навигации
        nav = GridLayout(cols=3, spacing=dp(8),
                         size_hint_y=None, height=dp(52))
        nav.add_widget(btn("⚙️ Доход",
                           on_press=lambda _: self.sm.go("income"),
                           bg=C["surface"]))
        nav.add_widget(btn("➕ Расход",
                           on_press=lambda _: self.sm.go("add"),
                           bg=C["accent"]))
        nav.add_widget(btn("📋 Список",
                           on_press=lambda _: self.sm.go("list"),
                           bg=C["surface"]))
        root.add_widget(nav)

        self.add_widget(root)

    def _stat_card(self, title, accent):
        box = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(2))
        with box.canvas.before:
            Color(*hex_c(C["card"]))
            box._rect = RoundedRectangle(pos=box.pos, size=box.size,
                                         radius=[dp(10)])
        box.bind(pos=lambda o, v: setattr(o._rect, "pos", v),
                 size=lambda o, v: setattr(o._rect, "size", v))
        box.title_lbl = lbl(title, size=dp(11), color=C["muted"],
                             halign="center")
        box.value_lbl = lbl("—", size=dp(15), bold=True,
                             color=accent, halign="center")
        box.add_widget(box.title_lbl)
        box.add_widget(box.value_lbl)
        return box

    def on_enter(self):
        self.refresh()

    def refresh(self):
        self.income_lbl.text  = f"Доход: {store.fmt(store.income)}"
        self.balance_lbl.text = (
            f"Остаток: {store.fmt(store.balance)}  •  "
            f"Потрачено: {store.fmt(store.total)}"
        )
        self.stat_income.value_lbl.text   = store.fmt(store.income)
        self.stat_expenses.value_lbl.text = store.fmt(store.total)
        bal = store.balance
        self.stat_balance.value_lbl.text  = store.fmt(bal)
        self.stat_balance.value_lbl.color = (
            hex_c(C["accent2"]) if bal >= 0 else hex_c(C["danger"])
        )

        self.cat_list.clear_widgets()
        totals = store.cat_totals()
        if not totals:
            self.cat_list.add_widget(
                lbl("Нет расходов", halign="center", color=C["muted"],
                    size_hint_y=None, height=dp(60)))
            return

        max_val = totals[0][1] if totals else 1
        for cat, amount in totals:
            color = CAT_COLORS.get(cat, C["muted"])
            row = BoxLayout(orientation="vertical",
                            size_hint_y=None, height=dp(56),
                            padding=[dp(12), dp(8)], spacing=dp(4))
            with row.canvas.before:
                Color(*hex_c(C["card"]))
                row._rect = RoundedRectangle(pos=row.pos, size=row.size,
                                             radius=[dp(10)])
            row.bind(pos=lambda o, v: setattr(o._rect, "pos", v),
                     size=lambda o, v: setattr(o._rect, "size", v))

            top = BoxLayout()
            top.add_widget(lbl(cat, size=dp(13)))
            top.add_widget(lbl(store.fmt(amount), size=dp(13),
                               bold=True, halign="right",
                               color=color))
            row.add_widget(top)

            # Полоска прогресса
            bar_bg = BoxLayout(size_hint_y=None, height=dp(4))
            with bar_bg.canvas.before:
                Color(*hex_c(C["border"]))
                bar_bg._r = RoundedRectangle(pos=bar_bg.pos, size=bar_bg.size,
                                             radius=[dp(2)])
            bar_bg.bind(pos=lambda o, v: setattr(o._r, "pos", v),
                        size=lambda o, v: setattr(o._r, "size", v))

            pct = amount / max_val if max_val else 0
            bar = Widget(size_hint=(pct, 1))
            with bar.canvas:
                Color(*hex_c(color))
                bar._r = RoundedRectangle(pos=bar.pos, size=bar.size,
                                          radius=[dp(2)])
            bar.bind(pos=lambda o, v: setattr(o._r, "pos", v),
                     size=lambda o, v: setattr(o._r, "size", v))
            bar_bg.add_widget(bar)
            row.add_widget(bar_bg)
            self.cat_list.add_widget(row)


# ──────────────────────────────────────────────
#  Экран 2: Установить доход
# ──────────────────────────────────────────────
class IncomeScreen(Screen):
    def __init__(self, sm, **kw):
        super().__init__(name="income", **kw)
        self.sm = sm
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=dp(24), spacing=dp(16))
        with root.canvas.before:
            Color(*hex_c(C["bg"]))
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda o, v: setattr(o._bg, "pos", v),
                  size=lambda o, v: setattr(o._bg, "size", v))

        root.add_widget(lbl("⚙️ Настройка дохода", size=dp(20),
                             bold=True, size_hint_y=None, height=dp(40)))
        root.add_widget(lbl("Ежемесячный доход", color=C["muted"],
                             size_hint_y=None, height=dp(24)))

        self.income_input = TextInput(
            text=str(int(store.income)) if store.income else "",
            hint_text="Например: 80000",
            input_filter="float",
            font_size=dp(18),
            background_color=hex_c(C["surface"]),
            foreground_color=hex_c(C["text"]),
            cursor_color=hex_c(C["accent"]),
            size_hint_y=None, height=dp(52),
            multiline=False,
        )
        root.add_widget(self.income_input)

        root.add_widget(lbl("Валюта", color=C["muted"],
                             size_hint_y=None, height=dp(24)))
        self.cur_spinner = Spinner(
            text=store.currency,
            values=["₽", "$", "€", "₸", "₴"],
            font_size=dp(16),
            background_normal="",
            background_color=hex_c(C["surface"]),
            color=hex_c(C["text"]),
            size_hint_y=None, height=dp(48),
        )
        root.add_widget(self.cur_spinner)

        root.add_widget(Widget())  # spacer

        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        row.add_widget(btn("← Назад",
                           on_press=lambda _: self.sm.go("home"),
                           bg=C["surface"]))
        row.add_widget(btn("💾 Сохранить",
                           on_press=self.save, bg=C["accent"]))
        root.add_widget(row)
        self.add_widget(root)

    def on_enter(self):
        self.income_input.text = str(int(store.income)) if store.income else ""
        self.cur_spinner.text  = store.currency

    def save(self, *_):
        try:
            store.income   = float(self.income_input.text or 0)
            store.currency = self.cur_spinner.text
            store.save()
            self.sm.go("home")
        except ValueError:
            pass


# ──────────────────────────────────────────────
#  Экран 3: Добавить расход
# ──────────────────────────────────────────────
class AddScreen(Screen):
    def __init__(self, sm, **kw):
        super().__init__(name="add", **kw)
        self.sm = sm
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=dp(24), spacing=dp(14))
        with root.canvas.before:
            Color(*hex_c(C["bg"]))
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda o, v: setattr(o._bg, "pos", v),
                  size=lambda o, v: setattr(o._bg, "size", v))

        root.add_widget(lbl("➕ Добавить расход", size=dp(20),
                             bold=True, size_hint_y=None, height=dp(40)))

        root.add_widget(lbl("Название", color=C["muted"],
                             size_hint_y=None, height=dp(22)))
        self.name_input = TextInput(
            hint_text="Например: Продукты",
            font_size=dp(16),
            background_color=hex_c(C["surface"]),
            foreground_color=hex_c(C["text"]),
            cursor_color=hex_c(C["accent"]),
            size_hint_y=None, height=dp(48),
            multiline=False,
        )
        root.add_widget(self.name_input)

        root.add_widget(lbl("Сумма", color=C["muted"],
                             size_hint_y=None, height=dp(22)))
        self.amount_input = TextInput(
            hint_text="0",
            input_filter="float",
            font_size=dp(16),
            background_color=hex_c(C["surface"]),
            foreground_color=hex_c(C["text"]),
            cursor_color=hex_c(C["accent"]),
            size_hint_y=None, height=dp(48),
            multiline=False,
        )
        root.add_widget(self.amount_input)

        root.add_widget(lbl("Категория", color=C["muted"],
                             size_hint_y=None, height=dp(22)))
        self.cat_spinner = Spinner(
            text=CAT_NAMES[0],
            values=CAT_NAMES,
            font_size=dp(15),
            background_normal="",
            background_color=hex_c(C["surface"]),
            color=hex_c(C["text"]),
            size_hint_y=None, height=dp(48),
        )
        root.add_widget(self.cat_spinner)

        self.error_lbl = lbl("", color=C["danger"],
                              halign="center", size_hint_y=None, height=dp(24))
        root.add_widget(self.error_lbl)

        root.add_widget(Widget())

        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        row.add_widget(btn("← Назад",
                           on_press=lambda _: self.sm.go("home"),
                           bg=C["surface"]))
        row.add_widget(btn("✅ Добавить",
                           on_press=self.add_expense, bg=C["accent"]))
        root.add_widget(row)
        self.add_widget(root)

    def on_enter(self):
        self.name_input.text   = ""
        self.amount_input.text = ""
        self.error_lbl.text    = ""

    def add_expense(self, *_):
        name   = self.name_input.text.strip()
        amount = self.amount_input.text.strip()

        if not name:
            self.error_lbl.text = "Введите название"
            return
        try:
            a = float(amount)
            if a <= 0:
                raise ValueError
        except ValueError:
            self.error_lbl.text = "Введите корректную сумму"
            return

        store.add_expense(name, a, self.cat_spinner.text)
        self.sm.go("home")


# ──────────────────────────────────────────────
#  Экран 4: Список расходов
# ──────────────────────────────────────────────
class ListScreen(Screen):
    def __init__(self, sm, **kw):
        super().__init__(name="list", **kw)
        self.sm = sm
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=dp(16), spacing=dp(10))
        with root.canvas.before:
            Color(*hex_c(C["bg"]))
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda o, v: setattr(o._bg, "pos", v),
                  size=lambda o, v: setattr(o._bg, "size", v))

        root.add_widget(lbl("📋 Все расходы", size=dp(20),
                             bold=True, size_hint_y=None, height=dp(40)))

        scroll = ScrollView(size_hint=(1, 1))
        self.expense_list = BoxLayout(orientation="vertical",
                                      spacing=dp(8), size_hint_y=None)
        self.expense_list.bind(
            minimum_height=self.expense_list.setter("height"))
        scroll.add_widget(self.expense_list)
        root.add_widget(scroll)

        root.add_widget(btn("← Назад",
                            on_press=lambda _: self.sm.go("home"),
                            bg=C["surface"],
                            size_hint_y=None, height=dp(50)))
        self.add_widget(root)

    def on_enter(self):
        self.refresh()

    def refresh(self):
        self.expense_list.clear_widgets()
        if not store.expenses:
            self.expense_list.add_widget(
                lbl("Расходов нет", halign="center", color=C["muted"],
                    size_hint_y=None, height=dp(60)))
            return

        for i, e in enumerate(reversed(store.expenses)):
            real_idx = len(store.expenses) - 1 - i
            color = CAT_COLORS.get(e["category"], C["muted"])

            row = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=dp(64),
                            padding=[dp(12), dp(8)], spacing=dp(8))
            with row.canvas.before:
                Color(*hex_c(C["card"]))
                row._rect = RoundedRectangle(pos=row.pos, size=row.size,
                                             radius=[dp(12)])
            row.bind(pos=lambda o, v: setattr(o._rect, "pos", v),
                     size=lambda o, v: setattr(o._rect, "size", v))

            # Цветной маркер
            mark = Widget(size_hint=(None, 1), width=dp(4))
            with mark.canvas:
                Color(*hex_c(color))
                mark._r = RoundedRectangle(pos=mark.pos, size=mark.size,
                                           radius=[dp(2)])
            mark.bind(pos=lambda o, v: setattr(o._r, "pos", v),
                      size=lambda o, v: setattr(o._r, "size", v))
            row.add_widget(mark)

            info = BoxLayout(orientation="vertical", spacing=dp(2))
            info.add_widget(lbl(e["name"], size=dp(14), bold=True))
            info.add_widget(lbl(f"{e['category']}  •  {e.get('date','')}",
                                size=dp(11), color=C["muted"]))
            row.add_widget(info)

            right = BoxLayout(orientation="vertical", size_hint_x=None,
                              width=dp(90), spacing=dp(4))
            right.add_widget(lbl(store.fmt(e["amount"]), size=dp(14),
                                 bold=True, color=color, halign="right"))

            del_btn = btn("🗑", bg=C["surface"],
                          size_hint=(None, None),
                          size=(dp(36), dp(28)))
            idx = real_idx

            def make_del(ii):
                def _del(_):
                    self._confirm_delete(ii)
                return _del

            del_btn.bind(on_press=make_del(idx))
            right.add_widget(del_btn)
            row.add_widget(right)

            self.expense_list.add_widget(row)

    def _confirm_delete(self, idx):
        content = BoxLayout(orientation="vertical",
                            padding=dp(16), spacing=dp(12))
        content.add_widget(lbl("Удалить расход?", halign="center",
                                bold=True, size_hint_y=None, height=dp(30)))
        name = store.expenses[idx]["name"]
        content.add_widget(lbl(name, halign="center",
                                color=C["muted"], size_hint_y=None, height=dp(24)))

        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        popup = Popup(title="", content=content,
                      size_hint=(0.8, None), height=dp(180),
                      background_color=hex_c(C["surface"]),
                      separator_height=0)

        def confirm(_):
            store.remove_expense(idx)
            popup.dismiss()
            self.refresh()

        btns.add_widget(btn("Отмена", on_press=lambda _: popup.dismiss(),
                            bg=C["surface"]))
        btns.add_widget(btn("Удалить", on_press=confirm, bg=C["danger"]))
        content.add_widget(btns)
        popup.open()


# ──────────────────────────────────────────────
#  Менеджер экранов
# ──────────────────────────────────────────────
class AppSM(ScreenManager):
    def __init__(self, **kw):
        super().__init__(transition=SlideTransition(), **kw)
        self._home  = HomeScreen(self)
        self._inc   = IncomeScreen(self)
        self._add   = AddScreen(self)
        self._list  = ListScreen(self)
        for s in (self._home, self._inc, self._add, self._list):
            self.add_widget(s)

    def go(self, name):
        self.current = name


# ──────────────────────────────────────────────
#  Приложение
# ──────────────────────────────────────────────
class ExpenseApp(App):
    def build(self):
        Window.clearcolor = hex_c(C["bg"])
        return AppSM()


if __name__ == "__main__":
    ExpenseApp().run()
