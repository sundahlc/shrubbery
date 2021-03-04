import streamlit as st
import pandas as pd
import psycopg2
import urllib.parse
import os

from streamlit.report_thread import get_report_ctx

class SessionState(object):
    def __init__(self, **kwargs):
        """A new SessionState object.

        Parameters
        ----------
        **kwargs : any
            Default values for the session state.

        Example
        -------
        >>> session_state = SessionState(user_name='', favorite_color='black')
        >>> session_state.user_name = 'Mary'
        ''
        >>> session_state.favorite_color
        'black'

        """
        for key, val in kwargs.items():
            setattr(self, key, val)


@st.cache(allow_output_mutation=True)
def get_session(id, **kwargs):
    return SessionState(**kwargs)


def get(**kwargs):
    """Gets a SessionState object for the current session.

    Creates a new object if necessary.

    Parameters
    ----------
    **kwargs : any
        Default values you want to add to the session state, if we're creating a
        new one.

    Example
    -------
    >>> session_state = get(user_name='', favorite_color='black')
    >>> session_state.user_name
    ''
    >>> session_state.user_name = 'Mary'
    >>> session_state.favorite_color
    'black'

    Since you set user_name above, next time your script runs this will be the
    result:
    >>> session_state = get(user_name='', favorite_color='black')
    >>> session_state.user_name
    'Mary'

    """
    ctx = get_report_ctx()
    id = ctx.session_id
    return get_session(id, **kwargs)

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

# @st.cache(allow_output_mutation=True)
# def load_player():
#     player_1 = player()
#     return player_1

session_state = get(session_player=player())

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
    cur.execute("select id, contents, type from cards where type = 'word' and checkedout = False order by random() limit 1")
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
    cur.execute('''select id, type, contents from cards where type = 'modifier' or type = 'foreshadow' 
                    and checkedout = False order by random() limit 1''')
    id, card_type, contents = cur.fetchone()
    cur.execute(f"update cards set checkedout = True where id = {id}")
    conn.commit()
    cur.close()
    return id, card_type, contents

def get_all_modifiers(conn):
    query = "SELECT contents, type FROM CARDS WHERE TYPE='modifier' OR TYPE='foreshadow' ORDER BY TYPE"
    modifiers = pd.read_sql(query, conn)
    return modifiers

conn = connect_to_elephantsql()

# player = load_player()

if st.sidebar.button('Shuffle my cards back'):
    cur = conn.cursor()
    sql = 'update cards set checkedout = False where '
    for card_id in session_state.session_player.checkedout_ids:
        sql = sql + f'id = {card_id} or '
    sql = sql[:len(sql)-4]
    cur.execute(sql) # remember to add functionality to only shuffle your cards back in
    conn.commit()
    cur.close()
    session_state.session_player.reset()
    
column_1, column_2 = st.beta_columns([1,2])
story_spot = column_2.empty()

if column_1.button('Hit me'):
    try:
        card_id, card_content, card_type = hit_me(conn)
        session_state.session_player.cards[f'{card_type} | {card_content}'] = False
        session_state.session_player.checkedout_ids.append(card_id)
        session_state.session_player.points = session_state.session_player.points - 1
    except:
        st.header('YOU RUN OUTTA CAHDS MATE')

if column_1.button('Gimme a modifier'):
    try:
        card_id, card_type, card_content = modifier(conn)
        session_state.session_player.cards[f'{card_type} | {card_content}'] = False
        session_state.session_player.checkedout_ids.append(card_id)
        session_state.session_player.points = session_state.session_player.points - 2
    except:
        st.header("ah man we're all out of modifiers")

if column_1.button('Story time'):
    try:
        card_id, card_content = story_time(conn)
        session_state.session_player.story = card_content
        session_state.session_player.checkedout_ids.append(card_id)
    except:
        st.header('YOU RUN OUTTA STORY CAHDS MATE')

if column_1.button('Burn this'):
    for card, ditch in session_state.session_player.cards.copy().items():
        if ditch:
            session_state.session_player.discard.append(card)
            _ = session_state.session_player.cards.pop(card)

for card in session_state.session_player.cards.keys():
    session_state.session_player.cards[card] = column_2.checkbox(card, key=card)
story_spot.markdown(f'### {session_state.session_player.story}')

session_state.session_player.points = column_2.number_input('points', min_value=0, max_value=None,
                                                            value=session_state.session_player.points)

player_name = st.sidebar.text_input(label='name')
if st.sidebar.button("I'm Mike"):
    if player_name.lower() == 'mike':
        st.table(get_all_modifiers(conn))

# st.sidebar.write(repr(player.__dict__))

conn.close()

st.sidebar.markdown('### Rules reminder')
rules = '''
Word card = 1 point
Modifier card = 2 points

### Judging:
Integrating your own cards: 
- 2 points each

Someone else integrates your cards:
- 2 points for a word,
- 3 points for a modifier

### Creating elements:
- 7 points for a character or other element
- 5 points for a trait
- 5 points to create your own modifier card
- 5 points to create your own story card'''

st.sidebar.markdown(rules)