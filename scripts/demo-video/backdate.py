import sqlite3
c = sqlite3.connect('/data/specboard.db')
def shift(table, days, where='1=1', cols=('created_at',)):
    for col in cols:
        c.execute(f"update {table} set {col} = strftime('%Y-%m-%d %H:%M:%f', {col}, '-{days} days') where {where}")
shift('projects', 6, 'id=1'); shift('projects', 0.1, 'id=1', ('updated_at',))
shift('projects', 12, 'id=2', ('created_at', 'updated_at')); shift('projects', 3, 'id=3'); shift('projects', 1, 'id=3', ('updated_at',))
shift('cards', 5, 'project_id=1')
shift('cards', 4, 'id in (1,2,3)', ('updated_at', 'done_at'))
shift('cards', 2, 'id=4', ('updated_at', 'started_at'))
shift('cards', 1, 'id=5', ('updated_at', 'started_at'))
shift('cards', 3, 'id in (6,7,8,9,10,11)', ('updated_at',))
shift('cards', 10, 'project_id=2', ('created_at', 'updated_at', 'done_at', 'started_at'))
shift('cards', 2, 'project_id=3', ('created_at', 'updated_at', 'done_at', 'started_at'))
shift('questions', 5, "project_id=1 and asked_by='specboard'", ('created_at', 'answered_at'))
shift('questions', 0.2, "asked_by='claude'")
c.execute("update activities set created_at = strftime('%Y-%m-%d %H:%M:%f', created_at, '-' || (5 - (id % 6) * 0.8) || ' days') where project_id=1")
c.execute("update activities set created_at = strftime('%Y-%m-%d %H:%M:%f', created_at, '-3 hours') where message like 'Grade de%'")
c.commit()
