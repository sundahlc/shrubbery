import streamlit as st
import pandas as pd
import psycopg2
import urllib.parse
import os

class player():
    def __init__(self):
        self.cards = {}
        self.story = ''
        self.discard = []
        self.checkedout_ids = []
        self.points = 20

    def reset(self):
        self.cards = {}
        self.story = ''
        self.discard = []
        self.checkedout_ids = []

@st.cache(allow_output_mutation=True)
def load_player():
    player_1 = player()
    return player_1

def connect_to_elephantsql():
    # Connect to ElephantSQL database
    urllib.parse.uses_netloc.append("postgres")
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
    except:
        DATABASE_URL = open(r'../shrubbery_login.txt', 'r').read().strip()
    url = urllib.parse.urlparse(DATABASE_URL)
    conn = psycopg2.connect(database=url.path[1:],
    user = url.username,
    password = url.password,
    host = url.hostname,
    port = url.port
    )

    return conn

def hit_me(conn):
    cur = conn.cursor()
    cur.execute("select id, contents, type from cards where type != 'story' and checkedout = False order by random() limit 1")
    id, contents, type = cur.fetchone()
    cur.execute(f"update cards set checkedout = True where id = {id}")
    conn.commit()
    cur.close()
    return id, contents, type

def story_time(conn):
    cur = conn.cursor()
    cur.execute("select id, contents from cards where type = 'story' and checkedout = False order by random() limit 1")
    id, contents = cur.fetchone()
    cur.execute(f"update cards set checkedout = True where id = {id}")
    conn.commit()
    cur.close()
    return id, contents

def modifier(conn):
    cur = conn.cursor()
    cur.execute("select id, contents from cards where type = 'modifier' and checkedout = False order by random() limit 1")
    id, contents = cur.fetchone()
    cur.execute(f"update cards set checkedout = True where id = {id}")
    conn.commit()
    cur.close()
    return id, contents

def get_all_modifiers(conn):
    query = "SELECT contents, type FROM CARDS WHERE TYPE='modifier' OR TYPE='foreshadow' ORDER BY TYPE"
    modifiers = pd.read_sql(query, conn)
    return modifiers

conn = connect_to_elephantsql()

player = load_player()

if st.sidebar.button('Shuffle my cards back'):
    cur = conn.cursor()
    sql = 'update cards set checkedout = False where '
    for card_id in player.checkedout_ids:
        sql = sql + f'id = {card_id} or '
    sql = sql[:len(sql)-4]
    cur.execute(sql) # remember to add functionality to only shuffle your cards back in
    conn.commit()
    cur.close()
    player.reset()
    
column_1, column_2 = st.beta_columns([1,2])
story_spot = column_2.empty()

if column_1.button('Hit me'):
    try:
        card_id, card_content, card_type = hit_me(conn)
        player.cards[f'{card_type} | {card_content}'] = False
        player.checkedout_ids.append(card_id)
    except:
        st.header('YOU RUN OUTTA CAHDS MATE')

if column_1.button('Gimme a modifier'):
    try:
        card_id, card_content = modifier(conn)
        player.cards[f'modifier | {card_content}'] = False
        player.checkedout_ids.append(card_id)
    except:
        st.header("ah man we're all out of modifiers")

if column_1.button('Story time'):
    try:
        card_id, card_content = story_time(conn)
        player.story = card_content
        player.checkedout_ids.append(card_id)
    except:
        st.header('YOU RUN OUTTA STORY CAHDS MATE')

if column_1.button('Burn this'):
    for card, ditch in player.cards.copy().items():
        if ditch:
            player.discard.append(card)
            _ = player.cards.pop(card)

for card in player.cards.keys():
    player.cards[card] = column_2.checkbox(card, key=card)
story_spot.markdown(f'### {player.story}')

player.points = st.sidebar.number_input('points', min_value=0, max_value=None, value=player.points)

player_name = st.sidebar.text_input(label='name')
if st.sidebar.button("I'm Mike"):
    if player_name.lower() == 'mike':
        st.table(get_all_modifiers(conn))

# st.sidebar.write(repr(player.__dict__))

conn.close()