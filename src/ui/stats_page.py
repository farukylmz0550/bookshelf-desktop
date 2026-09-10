# Katip Celebi — the statistics page.
# License: GPL-3.0-or-later (see LICENSE).

"""Metric cards, reading goals, and pie charts of the collection.

Charts come from matplotlib over its GTK4Agg backend; if matplotlib is
missing the page still shows the numbers, just without the pies.
"""

from datetime import date

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from core import summary
from core.reading import format_duration
from shared.texts import text


WINDOWS = (("365", 365), ("30", 30))
SLICE_COLOURS = ("#9141ac", "#3584e4", "#33d17a", "#ff7800", "#e01b24")


class MetricCard(Gtk.Box):
    """A number and the words that explain it."""

    def __init__(self, caption: str):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=2,
            margin_all=6, css_classes=["card"], valign=Gtk.Align.START,
        )
        self.caption = Gtk.Label(label=caption, css_classes=["dim-label"])
        self.append(self.caption)
        self.value = Gtk.Label(css_classes=["title-3"])
        self.append(self.value)

    def set(self, value: str) -> None:
        self.value.set_text(value)


class StatsPage(Gtk.Box):
    """What the library says about how it gets read."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_all=12)
        self.window = window
        self.cards: dict[str, MetricCard] = {}

        metrics = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=4)
        for key, label in (
            ("read", "metric_read"), ("reading", "metric_reading"), ("want", "metric_want"),
            ("not_read", "metric_not_read"), ("this_month", "metric_this_month"),
            ("this_year", "metric_this_year"), ("average", "metric_average"),
            ("total", "metric_total"),
        ):
            card = MetricCard(text(key))
            self.cards[key] = card
            metrics.append(card)
        self.append(metrics)

        goals = Adw.PreferencesGroup(title=text("goals_heading"))
        goals.add(self._goal_row("goal_yearly", self._save_yearly))
        goals.add(self._goal_row("goal_monthly", self._save_monthly))
        self.append(goals)

        charts_row = Gtk.Box(spacing=6)
        self.window_combo = Gtk.DropDown(model=Gtk.StringList.new([text(f"window_{k}") for k, _ in WINDOWS]))
        self.window_combo.connect("notify::selected", lambda d, _p: self.refresh())
        charts_row.append(self.window_combo)
        self.append(charts_row)

        self.chart_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, vexpand=True)
        self.append(self.chart_box)
        self.refresh()

    def _goal_row(self, key: str, save) -> Gtk.Widget:
        row = Adw.ActionRow(title=text(key))
        spin = Gtk.SpinButton.new_with_range(0, 9999, 1)
        spin.set_value(getattr(self.window.goals, key.split("_")[1]) or 0)
        spin.connect("value-changed", lambda s: save(s.get_value_as_int()))
        row.add_suffix(spin)
        self.goal_progress = Gtk.ProgressBar(show_text=True)
        self.progress_of = getattr(self, "progress_of", {})
        self.progress_of[key] = self.goal_progress
        row.add_suffix(self.goal_progress)
        return row

    def _save_yearly(self, value: int) -> None:
        self.window.goals.set_yearly(value)
        self.refresh()

    def _save_monthly(self, value: int) -> None:
        self.window.goals.set_monthly(value)
        self.refresh()

    def refresh(self) -> None:
        books = self.window.library.books
        today = date.today()
        ledger = self.window.ledger
        counts = summary.counts_by_status(books)
        finished = summary.finished_in_month(books, today.year, today.month)
        average = summary.average_days_to_finish(books)
        cards = {
            "read": str(counts["read"]),
            "reading": str(counts["reading"]),
            "want": str(counts["want_to_read"]),
            "not_read": str(counts["not_read"]),
            "this_month": str(finished),
            "this_year": str(summary.finished_in_year(books, today.year)),
            "average": text("metric_no_average") if average is None else format_duration(average),
            "total": text("metric_total").format(n=len(books)),
        }
        for key, value in cards.items():
            self.cards[key].set(value)
        yearly = summary.year_goal(books, self.window.goals.yearly)
        monthly = summary.month_goal(books, self.window.goals.monthly)
        self._show_goal("goal_yearly", yearly)
        self._show_goal("goal_monthly", monthly)
        self._draw_charts()

    def _show_goal(self, key, goal) -> None:
        bar = self.progress_of.get(key)
        if bar is None:
            return
        bar.set_text(text("goal_progress").format(done=goal.done, target=goal.target))
        bar.set_fraction(min(goal.fraction, 1.0))

    def _draw_charts(self) -> None:
        window_days = WINDOWS[self.window_combo.get_selected()][1]
        books = self.window.library.books
        series = {
            text("chart_time"): summary.time_spent(books, window_days),
            text("chart_authors"): summary.top_authors(books),
            text("chart_publishers"): summary.top_publishers(books),
            text("chart_tags"): summary.tag_spread(books),
        }
        for child in list(self.chart_box):
            self.chart_box.remove(child)
        any_drawn = False
        for title, pairs in series.items():
            if not pairs:
                continue
            any_drawn = True
            self.chart_box.append(self._chart(title, pairs))
        if not any_drawn:
            self.chart_box.append(Gtk.Label(label=text("stats_empty")))

    def _chart(self, title: str, pairs) -> Gtk.Widget:
        try:
            import matplotlib
            matplotlib.use("GTK4Agg")
            from matplotlib.backends.backend_gtk4agg import FigureCanvasGTK4Agg
            from matplotlib.figure import Figure
        except Exception:
            label = Gtk.Label(label=f"{title}: " + "; ".join(f"{k} ({v})" for k, v in pairs))
            label.set_wrap(True)
            return label
        figure = Figure(figsize=(4.2, 3.2), layout="constrained")
        axis = figure.add_subplot()
        labels = [k or text("chart_untitled") for k, v in pairs]
        values = [max(v, 0.01) for k, v in pairs]
        axis.pie(values, labels=labels, colors=SLICE_COLOURS,
                 wedgeprops={"linewidth": 0}, textprops={"fontsize": 8})
        axis.set_title(title, fontsize=9)
        return FigureCanvasGTK4Agg(figure)
