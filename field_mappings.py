"""
Mapping of Japanese hololyzer table labels to (field_name, field_type).
field_type is one of: 'date', 'string', 'int', 'percent', 'float'
Lines ending with '†' require special handling (listed separately in SPECIAL_MAPPINGS).
"""

# Simple label → (field_name, field_type) mappings
LABEL_MAP = {
    # Dates
    '\u516c\u958b\u65e5\u6642':   ('public_time',    'date'),    # 公開日時
    '\u958b\u59cb\u65e5\u6642':   ('start_time',     'date'),    # 開始日時
    '\u7d42\u4e86\u65e5\u6642':   ('end_time',       'date'),    # 終了日時

    # Simple values
    '\u52d5\u753b\u6642\u9593':   ('total_time',     'string'),  # 動画時間

    # Chat counts
    '\u7dcf\u30c1\u30e3\u30c3\u30c8\u6570':           ('chat_num_total',  'int'),  # 総チャット数
    '\u30c1\u30e3\u30c3\u30c8\u6570\uff08\u65e5\u672c\u8a9e\uff09': ('chat_num_ja',     'int'),  # チャット数（日本語）
    '\u30c1\u30e3\u30c3\u30c8\u6570\uff08\u30b9\u30bf\u30f3\u30d7\uff09': ('chat_num_emoji',  'int'),  # チャット数（スタンプ）
    '\u30c1\u30e3\u30c3\u30c8\u6570\uff08\u82f1\u8a9e\uff09': ('chat_num_en',     'int'),  # チャット数（英語）

    # User counts
    '\u30e6\u30cb\u30fc\u30af\u30e6\u30fc\u30b6\u30fc\u6570': ('uniq_user_num',   'int'),  # ユニークユーザー数
    '\u30e6\u30cb\u30fc\u30af\u30e1\u30f3\u30d0\u30fc\u6570': ('uniq_member_num',  'int'),  # ユニークメンバー数

    # Super chat
    '\u7dcf\u30b9\u30d1\u30c1\u30e3\u91d1\u984d': ('total_super_chat_amount_yen', 'int'),  # 総スパチャ金額

    # Ratios
    '\u82f1\u8a9e\u30b3\u30e1\u7387':     ('english_chat_ratio', 'percent'),  # 英語コメ率
    '\u30e1\u30f3\u30d0\u30fc\u30b3\u30e1\u7387': ('member_chat_ratio',  'percent'),  # メンバーコメ率

    # Averages / max
    '\u5e73\u5747\u6bce\u79d2\u30b3\u30e1\u6570': ('chat_per_second', 'float'),  # 平均毎秒コメ数
    '\u6700\u5927\u540c\u63a5':       ('max_ccv',         'int'),    # 最大同接

    # Membership
    '\u30e1\u30f3\u30b7\u5165\u308a':     ('member_num',      'int'),    # メンシ入り

    # Milestone
    '\u30de\u30a4\u30eb\u30b9\u30c8\u30fc\u30f3': ('milestone_num', 'int'),    # マイルストーン
}

# Special: メンシギフト needs regex extraction for from/to values
