import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import json
import os
from datetime import datetime
from contextlib import contextmanager
import textwrap

@contextmanager
def writable_file(filepath):
    """ファイルを一時的に書き込み可能にする"""
    try:
        if os.path.exists(filepath):
            os.chmod(filepath, 0o644)
        yield
    finally:
        try:
            os.chmod(filepath, 0o444)
        except:
            pass

class CategoryDialog(tk.Toplevel):
    """属性管理ダイアログ"""
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.title("属性の編集")
        self.geometry("400x300")
        self.categories = categories.copy()
        self.result = None
        
        # リストボックス
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(list_frame, text="属性一覧:", font=("Arial", 10)).pack(anchor=tk.W)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, font=("Arial", 11), yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        self.refresh_list()
        
        # ボタン
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(button_frame, text="追加", command=self.add_category, 
                 bg="#4CAF50", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="名前変更", command=self.rename_category,
                 bg="#FF9800", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="削除", command=self.delete_category,
                 bg="#f44336", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="完了", command=self.on_ok,
                 bg="#2196F3", fg="white", padx=15, pady=5).pack(side=tk.RIGHT, padx=2)
        
        self.transient(parent)
        self.grab_set()
    
    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for cat in self.categories:
            self.listbox.insert(tk.END, cat)
    
    def add_category(self):
        name = simpledialog.askstring("属性の追加", "新しい属性名を入力してください:", parent=self)
        if name and name.strip():
            name = name.strip()
            if name not in self.categories:
                self.categories.append(name)
                self.refresh_list()
            else:
                messagebox.showwarning("警告", "その属性名は既に存在します。")
    
    def rename_category(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "名前を変更する属性を選択してください。")
            return
        
        old_name = self.categories[selection[0]]
        new_name = simpledialog.askstring("属性名の変更", 
                                         f"「{old_name}」の新しい名前を入力してください:", 
                                         parent=self, initialvalue=old_name)
        if new_name and new_name.strip():
            new_name = new_name.strip()
            if new_name != old_name:
                if new_name not in self.categories:
                    self.categories[selection[0]] = new_name
                    self.refresh_list()
                else:
                    messagebox.showwarning("警告", "その属性名は既に存在します。")
    
    def delete_category(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除する属性を選択してください。")
            return
        
        cat_name = self.categories[selection[0]]
        result = messagebox.askyesno("確認", f"「{cat_name}」を削除してもよろしいですか？")
        if result:
            del self.categories[selection[0]]
            self.refresh_list()
    
    def on_ok(self):
        self.result = self.categories
        self.destroy()

class MemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("メモ帳アプリ（改善版）")
        self.root.geometry("1200x650")
        
        self.data_file = "memos.json"
        self.memos = {}
        self.categories = []
        self.load_data()
        
        self.current_memo_id = None
        self.is_modified = False
        self.sort_key = "timestamp"
        self.sort_reverse = True
        
        self.setup_ui()
        self.refresh_memo_list()
        
        # 変更検知のためのバインディング
        self.title_entry.bind('<KeyRelease>', self.on_content_change)
        self.content_text.bind('<KeyRelease>', self.on_content_change)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        # ショートカットキー
        self.root.bind('<Control-s>', lambda e: self.save_current_memo())
    
    def load_data(self):
        """JSONファイルからデータを読み込む"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memos = data.get("memos", {})
                    self.categories = data.get("categories", [])
            except:
                self.memos = {}
                self.categories = []
        
        # 古いデータの互換性対応
        for memo_id, memo in self.memos.items():
            if "category" not in memo:
                memo["category"] = ""
    
    def save_data(self):
        """JSONファイルにデータを保存（コンテキストマネージャ使用）"""
        try:
            with writable_file(self.data_file):
                data = {
                    "memos": self.memos,
                    "categories": self.categories
                }
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("エラー", f"保存に失敗しました: {str(e)}")
    
    def setup_ui(self):
        """改善されたUIの構築"""
        # メインフレーム
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側：メモ編集エリア
        left_frame = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 属性選択（Combobox + 検索/置換ボタン同じ行）
        category_frame = tk.Frame(left_frame)
        category_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(category_frame, text="属性:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            category_frame, textvariable=self.category_var,
            values=[""] + self.categories, state="readonly",
            font=("Arial", 10), width=20
        )
        self.category_combo.pack(side=tk.LEFT, padx=(5, 0))

        # 右端に詰めて検索/置換ボタンを配置
        category_frame.grid_columnconfigure(2, weight=1)  # packを使っているので不要なら削除可
        tk.Button(
            category_frame, text="検索/置換",
            command=self.open_search_replace,
            bg="#FF9800", fg="white", padx=10, pady=3
        ).pack(side=tk.RIGHT)

        # タイトル入力
        title_frame = tk.Frame(left_frame)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(title_frame, text="タイトル:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.title_entry = tk.Entry(title_frame, font=("Arial", 12))
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 内容入力
        content_frame = tk.Frame(left_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(content_frame, text="内容:", font=("Arial", 10)).pack(anchor=tk.W)
        self.content_text = scrolledtext.ScrolledText(content_frame, font=("Arial", 11), wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 保存ボタン
        save_button_frame = tk.Frame(left_frame)
        save_button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        self.save_button = tk.Button(save_button_frame, text="保存 (Ctrl+S)", font=("Arial", 12, "bold"), 
                                   command=self.save_current_memo, bg="#2196F3", fg="white", 
                                   relief=tk.RAISED, padx=30, pady=8)
        self.save_button.pack(expand=True)
        
        # 右側：メモ一覧エリア
        right_frame = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.config(width=600)
        right_frame.pack_propagate(False)
        
        # タイトルと属性編集ボタン
        title_header = tk.Frame(right_frame)
        title_header.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        tk.Label(title_header, text="メモ一覧", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        tk.Button(title_header, text="属性を編集", command=self.edit_categories,
                 bg="#9C27B0", fg="white", font=("Arial", 9), padx=10, pady=2).pack(side=tk.RIGHT)
        
        # ソートボタン
        sort_frame = tk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=1)
        sort_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.sort_category_btn = tk.Button(sort_frame, text="属性", font=("Arial", 9),
                                         command=lambda: self.change_sort("category"),
                                         relief=tk.FLAT, padx=5, pady=2)
        self.sort_category_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.sort_title_btn = tk.Button(sort_frame, text="タイトル", font=("Arial", 9),
                                      command=lambda: self.change_sort("title"),
                                      relief=tk.FLAT, padx=5, pady=2)
        self.sort_title_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.sort_time_btn = tk.Button(sort_frame, text="時刻", font=("Arial", 9),
                                     command=lambda: self.change_sort("timestamp"),
                                     relief=tk.FLAT, padx=5, pady=2)
        self.sort_time_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                # リストボックス（属性・タイトル・時刻を3本に分ける）
        list_frame = tk.Frame(right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 共通スクロールバー
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 属性リスト
        frame_attr = tk.Frame(list_frame)
        frame_attr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.list_attr = tk.Listbox(
            frame_attr, exportselection=False,
            font=("Meiryo", 10), yscrollcommand=scrollbar.set
        )
        self.list_attr.pack(fill=tk.BOTH, expand=True)

        # タイトルリスト
        frame_title = tk.Frame(list_frame)
        frame_title.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.list_title = tk.Listbox(
            frame_title, exportselection=False,
            font=("Meiryo", 10), yscrollcommand=scrollbar.set
        )
        self.list_title.pack(fill=tk.BOTH, expand=True)

        # 時刻リスト
        frame_time = tk.Frame(list_frame)
        frame_time.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.list_time = tk.Listbox(
            frame_time, exportselection=False,
            font=("Meiryo", 10), yscrollcommand=scrollbar.set
        )
        self.list_time.pack(fill=tk.BOTH, expand=True)

        # スクロールを3本に同期
        def on_scroll(*args):
            self.list_attr.yview(*args)
            self.list_title.yview(*args)
            self.list_time.yview(*args)

        scrollbar.config(command=on_scroll)

        # 選択も3本同期
        self.list_attr.bind('<<ListboxSelect>>', self.on_memo_select)
        self.list_title.bind('<<ListboxSelect>>', self.on_memo_select)
        self.list_time.bind('<<ListboxSelect>>', self.on_memo_select)

        
        # ボタンフレーム
        button_frame = tk.Frame(right_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        self.new_button = tk.Button(button_frame, text="新規", font=("Arial", 11), 
                                   command=self.create_new_memo, bg="#4CAF50", fg="white", 
                                   relief=tk.RAISED, padx=20, pady=5)
        self.new_button.pack(side=tk.LEFT, expand=True, padx=(0, 5))
        
        self.delete_button = tk.Button(button_frame, text="削除", font=("Arial", 11), 
                                      command=self.delete_memo, bg="#f44336", fg="white",
                                      relief=tk.RAISED, padx=20, pady=5)
        self.delete_button.pack(side=tk.RIGHT, expand=True, padx=(5, 0))
        
        self.update_sort_buttons()
    
    def update_category_menu(self):
        """Combobox値更新（簡潔）"""
        self.category_combo['values'] = [""] + self.categories
    
    def on_category_change(self, event):
        """カテゴリ変更時の変更検知"""
        self.is_modified = True
    
    def open_search_replace(self):
        """検索置換ダイアログ"""
        dialog = tk.Toplevel(self.root)
        dialog.title("検索/置換")
        dialog.geometry("380x480")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="検索:", font=("Arial", 10)).pack(pady=(15, 5))
        find_var = tk.StringVar()
        find_entry = tk.Entry(dialog, textvariable=find_var, width=35, font=("Arial", 10))
        find_entry.pack(pady=5)
        find_entry.focus()
        
        tk.Label(dialog, text="置換:", font=("Arial", 10)).pack(pady=(10, 5))
        replace_var = tk.StringVar()
        replace_entry = tk.Entry(dialog, textvariable=replace_var, width=35, font=("Arial", 10))
        replace_entry.pack(pady=5)
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=15)
        
        def do_replace_all():
            find_text = find_var.get()
            replace_text = replace_var.get()
            if find_text:
                content = self.content_text.get("1.0", tk.END)
                new_content = content.replace(find_text, replace_text)
                self.content_text.delete("1.0", tk.END)
                self.content_text.insert("1.0", new_content)
                self.is_modified = True
                messagebox.showinfo("完了", f"{content.count(find_text)}箇所を置換しました。")
                dialog.destroy()
        
        def do_find_next():
            find_text = find_var.get()
            if find_text:
                content = self.content_text.get("1.0", tk.END)
                start = self.content_text.index(tk.INSERT)
                pos = content.find(find_text, int(start.split('.')[0]) * 1000)
                if pos != -1:
                    self.content_text.tag_remove("sel", "1.0", tk.END)
                    self.content_text.tag_add("sel", f"1.0+{pos}c", f"1.0+{pos+len(find_text)}c")
                    self.content_text.see(f"1.0+{pos}c")
                else:
                    messagebox.showinfo("検索", "見つかりません")
        
        tk.Button(button_frame, text="すべて置換", command=do_replace_all,
                  bg="#2196F3", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="次を検索", command=do_find_next,
                  bg="#FF9800", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="キャンセル", command=dialog.destroy,
                  bg="#757575", fg="white", padx=15, pady=5).pack(side=tk.RIGHT, padx=5)
    
    def edit_categories(self):
        """属性編集ダイアログ（改善版：辞書マッピング）"""
        dialog = CategoryDialog(self.root, self.categories)
        self.root.wait_window(dialog)
        
        if dialog.result is not None:
            old_categories = self.categories.copy()
            self.categories = dialog.result
            
            # 辞書マッピングで安全に置換
            old_to_new = {}
            for i, old_cat in enumerate(old_categories):
                if i < len(self.categories):
                    old_to_new[old_cat] = self.categories[i]
            
            for memo in self.memos.values():
                old_category = memo.get("category", "")
                if old_category in old_to_new:
                    memo["category"] = old_to_new[old_category]
                elif old_category not in self.categories:
                    memo["category"] = ""  # 削除された属性をクリア
            
            self.save_data()
            self.update_category_menu()
            self.refresh_memo_list()
    
    def change_sort(self, key):
        """ソート方法を変更"""
        if self.sort_key == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = key
            self.sort_reverse = False if key in ["category", "title"] else True
        
        self.update_sort_buttons()
        self.refresh_memo_list()
    
    def update_sort_buttons(self):
        """ソートボタンの表示を更新"""
        # すべてのボタンをリセット
        self.sort_category_btn.config(text="属性", bg="SystemButtonFace")
        self.sort_title_btn.config(text="タイトル", bg="SystemButtonFace")
        self.sort_time_btn.config(text="時刻", bg="SystemButtonFace")
        
        # アクティブなボタンを強調
        arrow = "▲" if not self.sort_reverse else "▼"
        if self.sort_key == "category":
            self.sort_category_btn.config(text=f"{arrow}属性", bg="#E3F2FD")
        elif self.sort_key == "title":
            self.sort_title_btn.config(text=f"{arrow}タイトル", bg="#E3F2FD")
        else:
            self.sort_time_btn.config(text=f"{arrow}時刻", bg="#E3F2FD")
    
    def on_content_change(self, event=None):
        """内容が変更されたことを記録"""
        self.is_modified = True
    
    def create_new_memo(self):
        """新規メモを作成"""
        if self.is_modified:
            result = messagebox.askyesnocancel("確認", 
                                              "編集中の内容があります。保存しますか？\n\n"
                                              "はい: 保存して新規作成\n"
                                              "いいえ: 保存せずに新規作成\n"
                                              "キャンセル: 新規作成を中止")
            
            if result is None:
                return
            elif result:
                if not self.save_current_memo():
                    return
        
        self.clear_fields()
        self.current_memo_id = None
        self.is_modified = False
        self.category_var.set("")
        self.title_entry.focus()
    
    def save_current_memo(self, event=None):
        """現在のメモを保存"""
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()
        category = self.category_var.get()
        
        if not title:
            messagebox.showwarning("警告", "タイトルを入力してください。")
            return False
        
        if not content:
            messagebox.showwarning("警告", "内容を入力してください。")
            return False
        
        # 新規または更新
        if self.current_memo_id is None:
            memo_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
            self.current_memo_id = memo_id
        else:
            memo_id = self.current_memo_id
        
        self.memos[memo_id] = {
            "title": title,
            "content": content,
            "category": category,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.save_data()
        self.refresh_memo_list()
        self.is_modified = False
        
        messagebox.showinfo("成功", "メモを保存しました。")
        return True
    
    def get_sorted_memos(self):
        """安定ソート改善版"""
        sorted_memos = list(self.memos.items())
        
        if self.sort_key == "category":
            # カテゴリ→タイムスタンプの安定ソート
            sorted_memos.sort(key=lambda x: (x[1].get("category", ""), x[1].get("timestamp", "")),
                            reverse=self.sort_reverse)
        elif self.sort_key == "title":
            # タイトル→タイムスタンプ
            sorted_memos.sort(key=lambda x: (x[1].get("title", ""), x[1].get("timestamp", "")),
                            reverse=self.sort_reverse)
        else:  # timestamp
            sorted_memos.sort(key=lambda x: x[1].get("timestamp", ""), reverse=self.sort_reverse)
        
        return sorted_memos
    
    def on_memo_select(self, event):
        """メモが選択されたときの処理（3本のリスト同期版）"""
        lb = event.widget
        selection = lb.curselection()
        if not selection:
            return

        index = selection[0]

        # 3本すべてで同じ行を選択状態にする
        for other in (self.list_attr, self.list_title, self.list_time):
            if other is not lb:
                other.selection_clear(0, tk.END)
                other.selection_set(index)

        # ここから先は従来通り、index からメモを特定して読み込む
        sorted_memos = self.get_sorted_memos()
        if index >= len(sorted_memos):
            return

        if self.is_modified:
            result = messagebox.askyesnocancel(
                "確認",
                "編集中の内容があります。保存しますか？\n\n"
                "はい: 保存して開く\n"
                "いいえ: 保存せずに開く\n"
                "キャンセル: 開くのを中止"
            )
            if result is None:
                return
            elif result:
                if not self.save_current_memo():
                    return

        memo_id, memo = sorted_memos[index]

        self.current_memo_id = memo_id
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, memo["title"])

        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", memo["content"])

        self.category_var.set(memo.get("category", ""))

        self.is_modified = False

    def delete_memo(self):
        """選択されたメモを削除"""
        selection = self.memo_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除するメモを選択してください。")
            return
        
        index = selection[0]
        sorted_memos = self.get_sorted_memos()
        
        if index < len(sorted_memos):
            memo_id, memo = sorted_memos[index]
            
            result = messagebox.askyesno("確認", 
                                       f"「{memo['title']}」を削除してもよろしいですか？")
            
            if result:
                del self.memos[memo_id]
                self.save_data()
                self.refresh_memo_list()
                
                if self.current_memo_id == memo_id:
                    self.clear_fields()
                    self.current_memo_id = None
                    self.is_modified = False
                
                messagebox.showinfo("成功", "メモを削除しました。")
    
    def refresh_memo_list(self):
        """メモ一覧を更新（3本のリストに分割表示）"""
        # まず全部消す
        for lb in (self.list_attr, self.list_title, self.list_time):
            lb.delete(0, tk.END)

        sorted_memos = self.get_sorted_memos()

        for memo_id, memo in sorted_memos:
            category = memo.get("category", "")
            title = memo.get("title", "")
            timestamp = memo.get("timestamp", "")

            # 時刻表示をこれまでと同じ形式に整形
            time_display = timestamp[5:16] if len(timestamp) >= 16 else timestamp

            self.list_attr.insert(tk.END, category)
            self.list_title.insert(tk.END, title)
            self.list_time.insert(tk.END, time_display)

    def clear_fields(self):
        """入力フィールドをクリア"""
        self.title_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)
        self.category_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()
