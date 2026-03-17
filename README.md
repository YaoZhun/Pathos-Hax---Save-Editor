# ⚔ pathosHax — Pathos: Nethack Codex 存檔編輯器

![pathosHax](https://img.shields.io/badge/version-3.0-green?style=flat-square)
![Python](https://img.shields.io/badge/python-3.9+-blue?style=flat-square)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square)

**pathosHax** 是一款為 [Pathos: Nethack Codex](https://pathos.azurewebsites.net/) 遊戲設計的存檔編輯器。
提供直覺的圖形介面，讓你輕鬆修改角色屬性、背包道具等存檔資料。

---

## ✨ 功能特色

| 功能 | 說明 |
|------|------|
| 🧙 **角色資訊** | 修改角色名稱、種族、職業、性別、陣營、等級 |
| ❤️ **HP / MP** | 調整生命值與魔力值，一鍵回滿 |
| 💪 **屬性值** | 滑桿 + 數字輸入，快速設定 STR / DEX / CON / INT / WIS / CHA |
| 🎒 **背包道具** | 新增、刪除、編輯道具，內建自動完成與快速新增 |
| 🪙 **金幣** | 直接修改金幣數量 |
| 📋 **備份** | 一鍵備份存檔（.bak） |
| 🎲 **範例存檔** | 載入範例存檔體驗功能 |

---

## 🖥 螢幕截圖

應用程式介面採用綠色終端風格（Hacker Theme），黑底綠字，致敬經典 Roguelike 遊戲。

---

## 🚀 快速開始

### 方法一：直接執行 Python

確保系統已安裝 Python 3.9+（macOS 已内建）：

```bash
cd pathosHax
python3 run.py
```

### 方法二：使用 macOS 應用程式（.app）

1. 安裝打包工具：
   ```bash
   pip3 install py2app
   ```

2. 建構 `.app`：
   ```bash
   python3 setup.py py2app
   ```

3. 生成的應用程式在 `dist/pathosHax.app`，可直接雙擊開啟，或拖入「應用程式」資料夾。

> **提示**：首次開啟時如出現「未識別的開發者」提示，請到  
> **系統偏好設定 → 安全性與隱私** 點選「仍要打開」。

---

## 📁 存檔位置

pathosHax 會自動偵測以下存檔路徑：

| 來源 | 路徑 |
|------|------|
| **App Store 版** | `~/Library/Containers/23F5B09B-.../Data/Library/Adventures/` |
| **Steam 版** | `~/Library/Application Support/Steam/userdata/<UID>/679300/` |

支援的存檔格式：`.Adventure`、`.adventure`、`.backup`

---

## 🗂 專案架構

```
pathosHax/
├── run.py           # 應用程式入口點
├── model.py         # 資料層：存檔解析 / 序列化 / 已知道具
├── view.py          # 視圖層：tkinter UI 介面
├── controller.py    # 控制層：業務邏輯
├── setup.py         # py2app 打包設定
├── icon.icns        # 應用程式圖標
└── README.md        # 本文件
```

採用 **MVC（Model-View-Controller）** 架構：

- **Model**（`model.py`）— 負責存檔的解析（`parse`）與序列化（`serialize`），以及已知道具清單
- **View**（`view.py`）— 純 UI 層，建構 tkinter 介面，透過回呼函數與 Controller 互動
- **Controller**（`controller.py`）— 連接 Model 與 View，處理檔案讀寫、欄位同步、背包操作

---

## 📄 存檔格式

Pathos 使用純文字存檔（`.Adventure`），重要的是 **玩家行**：

```
character @[000001] "Aldric" level 7 [male] [human] [barbarian]
  glyph [human male barbarian] chaotic life 45 mana 12
  [str] 18 [dex] 14 [con] 16 [int] 10 [wis] 12 [cha] 9
  inventory { [long sword], [leather armour], [potion of healing] }
  square map [_level//depth_ 1] (04,23);
```

pathosHax 只修改這一行的內容，其餘資料完整保留。

---

## ⚠️ 注意事項

- **建議先備份**：修改前請使用「📋 備份」功能或手動複製存檔
- **遊戲版本**：存檔格式可能隨 Pathos 更新而改變
- **僅限單人存檔**：編輯器修改的是本地存檔，不影響線上排行榜

---

## 🛠 開發指引

### 環境需求

- Python 3.9+
- tkinter（macOS 已內建）
- py2app（僅打包時需要）

### 常用指令

```bash
# 開發模式執行
python3 run.py

# 打包為 .app（開發模式，快速）
python3 setup.py py2app -A

# 打包為 .app（正式版，獨立）
python3 setup.py py2app

# 清理打包產物
rm -rf build dist .eggs
```

---

## 📜 授權

本專案採用 [MIT License](https://opensource.org/licenses/MIT) 授權。

pathosHax 為第三方社群工具，與 Pathos: Nethack Codex 官方無關。
