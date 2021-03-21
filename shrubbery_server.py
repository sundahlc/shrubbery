import pandas as pd
from datetime import datetime
import psycopg2
import urllib.parse
import os

import streamlit as st
from streamlit.hashing import _CodeHasher

try:
    # Before Streamlit 0.65
    from streamlit.ReportThread import get_report_ctx
    from streamlit.server.Server import Server
except ModuleNotFoundError:
    # After Streamlit 0.65
    from streamlit.report_thread import get_report_ctx
    from streamlit.server.server import Server

#======================================================================================================================
# MAIN PAGE
#======================================================================================================================

# os.chdir(r'C:\Users\Kuri y Rizu\Documents\Synced Folders\Programming\shrubbery\shrubbery')

def main():
    state = _get_state()

    loader_name = st.sidebar.text_input('name')
    # if st.sidebar.button('Load me up Scottie'):
    load_player(state, loader_name)
    st.sidebar.write(repr(state.player.__dict__))

    get_game_state(state)

    if state.player.active == True:
        if st.checkbox("it's your turn", value=False):
            active_player(state)

    show_columns(state)

    st.sidebar.write(repr(state.__dict__))
    if st.sidebar.button('Clear state'):
        state.clear()

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()


#======================================================================================================================
# Database class
#======================================================================================================================


class db_talker():
    '''
    Usage:
    with db_talker() as cur:
        cur.execute(...)
    Automatically closes at the end of with block.
    '''

    def __enter__(self):
        self.conn = self.connect_to_elephantsql()
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, *args):
        self.conn.commit()
        self.conn.close()

    def connect_to_elephantsql(self):
        # Connect to ElephantSQL database
        urllib.parse.uses_netloc.append("postgres")
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
        except KeyError:
            DATABASE_URL = open(r'../shrubbery_login.txt', 'r').read().strip()
        url = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(database=url.path[1:],
        user = url.username,
        password = url.password,
        host = url.hostname,
        port = url.port
        )

        return conn


#======================================================================================================================
# PLAYER definitions
#======================================================================================================================


class player():
    def __init__(self, name):
        self.name = name.lower()
        self.cards = {}
        self.story = ''
        self.points = 5
        self.active = False

        with db_talker() as cur:
            cur.execute(f'''insert into players (name, active)
                            values ('{self.name}', false)
                            on conflict do nothing''')
            cur.execute(f'''select id from players where name = '{self.name}' ''')
            self.player_id = cur.fetchone()[0]

            cur.execute(f'''select points from players where id={self.player_id}''')
            self.points = cur.fetchone()[0]

    def reset(self):
        self.cards = {}
        self.selected = {}
        self.story = ''



#======================================================================================================================
# Button Definitions
#======================================================================================================================


def load_player(state, name):
    name = name.lower()
    if name not in ('chris', 'mike', 'nick', 'christian'):
        st.sidebar.write("You're not really in this game!")
        st.stop()
    state.player = player(name)
    with db_talker() as cur:
        cur.execute(f'''select cards.id, contents, type 
                        from players join cards
                        on players.id = cards.status
                        where players.id = {state.player.player_id}''')
        raw_hand_cards = cur.fetchall()

        cur.execute(f'''select active from players where id = {state.player.player_id}''')
        state.player.active = cur.fetchone()[0]

    for card in raw_hand_cards:
        id, contents, type = card
        state.player.cards[id] = type + ' | ' + contents


def draw_card(state, deck):
    with db_talker() as cur:
        cur.execute(f'''select id, contents, type from cards where deck = '{deck}' and status is NULL 
                        order by random() limit 1''')
        card_id, contents, type = cur.fetchone()
        cur.execute(f"update cards set status = {state.player.player_id} where id = {card_id}")

        state.player.points = state.player.points - 1
        cur.execute(f'''update players set points={state.player.points} where id={state.player.player_id}''')
        # cur.execute(f"insert into hands (player_id, card_id) values ({state.player.player_id}, {card_id}")

    state.player.cards[card_id] = type + ' | ' + contents


def act_on_card(state, action, card_id):
    choices = {'discard':-1, 'send':0}
    state.player.cards.pop(card_id)
    with db_talker() as cur:
        cur.execute(f'''update cards set status={choices[action]} where id={card_id}''')
        # cur.execute(f'''delete from hands where player_id={state.player.player_id} and card_id={card_id}''')


def get_game_state(state):
    with db_talker() as cur:
        cur.execute('''select status from turn''')
        state.turn = cur.fetchone()[0]

#======================================================================================================================
# Display flow
#======================================================================================================================

def active_player(state):
    st.markdown(f"## HEY {state.player.name.upper()}! You're the active player!")
    with db_talker() as cur:
        cur.execute('select type, contents from cards where status=0')
        active_cards = cur.fetchall()
    st.write(f"You have {len(active_cards)} cards sent ... so far.")
    st.button('Refresh! Do I have more cards?')
    if st.button('See your cards & WRITE (timer starts immediately!)'):
        state.turn = 'writing'
        with db_talker() as cur:
            cur.execute("update turn set status='writing'")
            cur.execute(f'update turn set time={datetime.timestamp(datetime.now())}')
    if state.turn == 'writing':
        st.success('GO!')
        for card in active_cards:
            type, contents = card
            st.write(type + ' | ' + contents)

        if st.button('stop writing'):
            state.turn = 'judging'
            end_writing(state)
    if state.turn == 'judging':
        minutes = str(round(state.writing_time // 60))
        seconds = str(round(state.writing_time % 60))
        if len(seconds) == 1:
            seconds = '0' + seconds
        st.write(f'You wrote for {minutes}:{seconds}.')

        if st.button('Pass turn'):
            state.turn='passing'
            with db_talker() as cur:
                cur.execute("update turn set status='passing'")
    if state.turn == 'passing':
        next_player = st.sidebar.selectbox('Next player is', ('chris', 'mike', 'nick', 'christian'))
        if st.sidebar.button('Pass to next player'):
            with db_talker() as cur:
                cur.execute('update players set active=false')
                cur.execute(f"update players set active=true where name='{next_player}'")
                cur.execute("update turn set status='accepting'")
            state.turn='accepting'


def end_writing(state):
    with db_talker() as cur:
        cur.execute("update turn set status='judging'")
        cur.execute('select time from turn')
        t1 = cur.fetchone()[0]
        cur.execute('update cards set status=-1 where status=0')

    t2 = datetime.timestamp(datetime.now())
    state.writing_time = t2 - t1


def show_columns(state):
    column_1, column_2 = st.beta_columns([1,2])

    # Left Column
    point_display = column_1.empty()
    deck_buttons = {'Story time':'story', 'Give me a normal card':'normal', 'How about a special card':'special'}
    for text, deck in deck_buttons.items():
        if column_1.button(text):
            draw_card(state, deck)

    # for action in ('Discard', 'Send'):
    if column_1.button('Discard'):
        for card_id, bool in state.selection.items():
            if bool == True:
                act_on_card(state, 'discard', card_id)

    if column_1.button('Send'):
        if state.turn == 'accepting':
            for card_id, bool in state.selection.items():
                if bool == True:
                    act_on_card(state, 'send', card_id)

        else:
            column_1.write("You can't send cards now!")

    real_points = point_display.number_input('Points', value=state.player.points, min_value=0, step=1)


    # Right Column
    state.selection = dict()
    for card_id, contents in state.player.cards.items():
        state.selection[card_id] = column_2.checkbox(contents, value=False)

    with db_talker() as cur:
        cur.execute(f'''update players set points={real_points} where id={state.player.player_id}''')

#======================================================================================================================
# Session State
#======================================================================================================================


class _SessionState:

    def __init__(self, session, hash_funcs):
        """Initialize SessionState instance."""
        self.__dict__["_state"] = {
            "data": {},
            "hash": None,
            "hasher": _CodeHasher(hash_funcs),
            "is_rerun": False,
            "session": session,
        }

    def __call__(self, **kwargs):
        """Initialize state data once."""
        for item, value in kwargs.items():
            if item not in self._state["data"]:
                self._state["data"][item] = value

    def __getitem__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __getattr__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __setitem__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def __setattr__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def clear(self):
        """Clear session state and request a rerun."""
        self._state["data"].clear()
        self._state["session"].request_rerun()

    def sync(self):
        """Rerun the app with all state values up to date from the beginning to fix rollbacks."""

        # Ensure to rerun only once to avoid infinite loops
        # caused by a constantly changing state value at each run.
        #
        # Example: state.value += 1
        if self._state["is_rerun"]:
            self._state["is_rerun"] = False

        elif self._state["hash"] is not None:
            if self._state["hash"] != self._state["hasher"].to_bytes(self._state["data"], None):
                self._state["is_rerun"] = True
                self._state["session"].request_rerun()

        self._state["hash"] = self._state["hasher"].to_bytes(self._state["data"], None)


def _get_session():
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")

    return session_info.session


def _get_state(hash_funcs=None):
    session = _get_session()

    if not hasattr(session, "_custom_session_state"):
        session._custom_session_state = _SessionState(session, hash_funcs)

    return session._custom_session_state


if __name__ == "__main__":
    main()