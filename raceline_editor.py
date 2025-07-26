import csv
import sys
import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET


def parse_lanelet2_osm(path):
    tree = ET.parse(path)
    root = tree.getroot()
    nodes = {}
    for node in root.findall('node'):
        node_id = node.get('id')
        local_x = None
        local_y = None
        for tag in node.findall('tag'):
            k = tag.get('k')
            if k == 'local_x':
                local_x = float(tag.get('v'))
            elif k == 'local_y':
                local_y = float(tag.get('v'))
        if local_x is not None and local_y is not None:
            nodes[node_id] = (local_x, local_y)
    ways = []
    for way in root.findall('way'):
        pts = []
        for nd in way.findall('nd'):
            ref = nd.get('ref')
            if ref in nodes:
                pts.append(nodes[ref])
        if len(pts) >= 2:
            ways.append(pts)
    return ways


def load_raceline_csv(path):
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    for row in rows:
        row['x'] = float(row['x'])
        row['y'] = float(row['y'])
    return reader.fieldnames, rows


class RaceLineEditor:
    def __init__(self, osm_path, csv_path):
        self.osm_path = osm_path
        self.csv_path = csv_path
        self.ways = parse_lanelet2_osm(osm_path)
        self.header, self.rows = load_raceline_csv(csv_path)
        self.points = [(r['x'], r['y']) for r in self.rows]
        self.root = tk.Tk()
        self.root.title('Racing Line Editor')
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg='white')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', self.redraw)
        self.point_ids = []
        self.line_id = None
        self.selected = None
        self.save_button = tk.Button(self.root, text='Save', command=self.save)
        self.save_button.pack(side='bottom')
        self.compute_bounds()
        self.redraw()

    def compute_bounds(self):
        xs = []
        ys = []
        for w in self.ways:
            for x, y in w:
                xs.append(x)
                ys.append(y)
        for x, y in self.points:
            xs.append(x)
            ys.append(y)
        self.min_x = min(xs)
        self.max_x = max(xs)
        self.min_y = min(ys)
        self.max_y = max(ys)

    def world_to_canvas(self, x, y):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        scale = min(w / (self.max_x - self.min_x), h / (self.max_y - self.min_y)) * 0.9
        off_x = (w - (self.max_x - self.min_x) * scale) / 2 - self.min_x * scale
        off_y = h - ((h - (self.max_y - self.min_y) * scale) / 2 + self.min_y * scale)
        cx = x * scale + off_x
        cy = -y * scale + off_y
        return cx, cy

    def canvas_to_world(self, cx, cy):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        scale = min(w / (self.max_x - self.min_x), h / (self.max_y - self.min_y)) * 0.9
        off_x = (w - (self.max_x - self.min_x) * scale) / 2 - self.min_x * scale
        off_y = h - ((h - (self.max_y - self.min_y) * scale) / 2 + self.min_y * scale)
        x = (cx - off_x) / scale
        y = -(cy - off_y) / scale
        return x, y

    def redraw(self, event=None):
        self.canvas.delete('all')
        # draw osm ways
        for way in self.ways:
            coords = []
            for x, y in way:
                cx, cy = self.world_to_canvas(x, y)
                coords.extend([cx, cy])
            if len(coords) >= 4:
                self.canvas.create_line(*coords, fill='gray')
        # draw racing line
        coords = []
        for x, y in self.points:
            cx, cy = self.world_to_canvas(x, y)
            coords.extend([cx, cy])
        if self.line_id:
            self.canvas.delete(self.line_id)
        if coords:
            self.line_id = self.canvas.create_line(*coords, fill='red', width=2)
        # draw points
        for pid in self.point_ids:
            self.canvas.delete(pid)
        self.point_ids = []
        for i, (x, y) in enumerate(self.points):
            cx, cy = self.world_to_canvas(x, y)
            pid = self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill='blue', outline='')
            self.canvas.tag_bind(pid, '<ButtonPress-1>', lambda e, idx=i: self.start_drag(idx, e))
            self.canvas.tag_bind(pid, '<B1-Motion>', lambda e, idx=i: self.drag(idx, e))
            self.canvas.tag_bind(pid, '<ButtonRelease-1>', lambda e, idx=i: self.end_drag(idx, e))
            self.point_ids.append(pid)

    def start_drag(self, idx, event):
        self.selected = idx

    def drag(self, idx, event):
        if self.selected is None:
            return
        cx = event.x
        cy = event.y
        x, y = self.canvas_to_world(cx, cy)
        self.points[idx] = (x, y)
        self.rows[idx]['x'] = x
        self.rows[idx]['y'] = y
        self.redraw()

    def end_drag(self, idx, event):
        self.selected = None

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile='edited_raceline.csv')
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.header)
                writer.writeheader()
                for row in self.rows:
                    writer.writerow(row)

    def run(self):
        self.root.mainloop()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Racing line editor')
    parser.add_argument('--osm', default='sample/lanelet2_map.osm')
    parser.add_argument('--csv', default='sample/raceline_awsim_30km.csv')
    parser.add_argument('--nogui', action='store_true', help='Only parse files and exit')
    args = parser.parse_args()
    if args.nogui:
        ways = parse_lanelet2_osm(args.osm)
        header, rows = load_raceline_csv(args.csv)
        print(f'Loaded {len(ways)} ways and {len(rows)} race points')
        return
    editor = RaceLineEditor(args.osm, args.csv)
    editor.run()


if __name__ == '__main__':
    main()
