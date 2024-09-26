import random
import time
import json
import os
import numpy as np
import requests
import sys
import copy
import jsonpickle
from collections import deque
from names_generator import generate_name
from coolname import generate_slug
import randomname
from pympler import asizeof


class Song:
    """
    Class for a song. It contains all the information directly related to a song.
    If song objects are compared with "==" ">" or "<" it will be based on the title.
    """
    def __init__(self, title, artist, album, genre, playtime=0, key="title"):
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.playtime = playtime
        self.key = key

    def set_key(self, key):
        # Define the key of "<", ">" or "==" comparison. Neccessary to be able to 
        # search/sort not only by title but also by artist, album and genre
        if key in ["title", "artist", "album", "genre", "playtime"]:
            self.key = key
        else:
            raise ValueError("Invalid sort key. Must be 'title', 'artist', 'album', 'genre' or 'playtime'.")

    def __str__(self):
        return (f"{self.title}, Artist: {self.artist}, Album: {self.album}, "
                f"Genre: {self.genre}, Playtime: {self.playtime/60:.2f} minutes")

    def __lt__(self, other):
        #return self.title < other.title
        return getattr(self, self.key) <  getattr(other, other.key)

    def __le__(self, other):
        # return self.title <= other.title
        return getattr(self, self.key) <= getattr(other, other.key)
    
    def __gt__(self, other):
        # return self.title > other.title
        return getattr(self, self.key) > getattr(other, other.key)

    def __ge__(self, other):
        return getattr(self, self.key) >= getattr(other, other.key)
        # return self.title >= other.title
    
    def __eq__(self, other):
        # return self.title == other.title
        return getattr(self, self.key) == getattr(other, other.key)


class Playlist:
    """
    The Playlist class organizes the songs in a sorted list, a binary search tree
    a red black tree and an AVL tree to enable efficient searching of songs with
    different algorithms. Moreover, it contains a copy of the song list in which 
    the songs can be shuffled and are unsorted. This list is useful for testing
    sorting algorithms. 
    This class organizes also the total playtime of the songs in the playlist and 
    the playlist name.
    """
    def __init__(self, name): 
        self.name = name
        self.total_time = 0
        self.songs_not_sorted = []  # Unsorted copy of song list for testing of sorting algorithms
        self.songs = []   # Sorted copy of song list for searching algorithms
        self.bst = BinarySearchTree()
        self.rbt = RedBlackTree()
        self.avl = AVLTree()

    def __str__(self):
        return f"{self.name}: contains {len(self.songs)} songs (total time: {self.total_time/60:.2f} minutes)"

    def __iter__(self):
        return iter(self.songs) 

    def __len__(self):
            return len(self.songs)
    
    def memory_usage(self):
        print(f"Memory usage in bytes of binary search tree (deep): {asizeof.asizeof(self.bst)}")
        print(f"Memory usage in bytes of AVL tree  (deep): {asizeof.asizeof(self.avl)}")
        print(f"Memory usage in bytes of red-black-tree (deep): {asizeof.asizeof(self.rbt)}")
        print(f"Memory usage in bytes of song list (deep): {asizeof.asizeof(self.songs)}")
        print(f"Memory usage in bytes of song list: {sys.getsizeof(self.songs)}")
        

class TreeNode:
    """
    Node for binary search tree
    """
    def __init__(self, song):
        self.song = song
        self.left = None
        self.right = None

class BinarySearchTree:
    """
    Implementation of binary search tree as given in the lecture.
    An depth first iterator was added to iterate over tree nodes based on 
    https://stackoverflow.com/questions/26145678/implementing-a-depth-first-tree-iterator-in-python 
    """
    def __init__(self):
        self.root = None
    
    def get_root(self):
        return self.root

    def insert(self, song):
        if self.root is None:
            self.root = TreeNode(song)
        else:
            self._insert_recursive(self.root, song)

    def _insert_recursive(self, node, song):
        if song < node.song:
            if node.left is None:
                node.left = TreeNode(song)
            else:
                self._insert_recursive(node.left, song)
        else:
            if node.right is None:
                node.right = TreeNode(song)
            else:
                self._insert_recursive(node.right, song)

    def search(self, song):
        return self._search_recursive(self.root, song)

    def _search_recursive(self, node, song):
        if node is None:
            return None
        if node.song == song:
            return node
        elif song < node.song:
            return self._search_recursive(node.left, song)
        else:
            return self._search_recursive(node.right, song)
    
    def node_depth_first_iter(self, node):
        """
        Quelle: https://stackoverflow.com/questions/26145678/implementing-a-depth-first-tree-iterator-in-python
        """
        stack = deque([node])
        while stack:
            node = stack.popleft()
            if node is not None:  
                yield node
                if node.right is not None:
                    stack.appendleft(node.right)
                if node.left is not None:
                    stack.appendleft(node.left)
     
    def __iter__(self):
        return self.node_depth_first_iter(self.root)

class RedBlackNode:
    """
    Node for Red black Tree
    """
    def __init__(self, song):
        self.song = song
        self.color = "RED"  # All newly inserted nodes are red by default
        self.left = None
        self.right = None
        self.parent = None

class RedBlackTree:
    """
    Red black tree as given in the lecture.
    The functionality to delete nodes was added.
    """
    def __init__(self):
        self.NIL = RedBlackNode(None)
        self.NIL.color = "BLACK"
        self.root = self.NIL
    
    def get_root(self):
        return self.root

    def insert(self, song):
        new_node = RedBlackNode(song)
        new_node.left = self.NIL
        new_node.right = self.NIL

        parent = None
        current = self.root

        while current != self.NIL:
            parent = current
            if new_node.song < current.song:
                current = current.left
            else:
                current = current.right

        new_node.parent = parent

        if parent is None:
            self.root = new_node
        elif new_node.song < parent.song:
            parent.left = new_node
        else:
            parent.right = new_node

        new_node.color = "RED"
        self.fix_insert(new_node)

    def fix_insert(self, node):
        while node != self.root and node.parent.color == "RED":
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right
                if uncle.color == "RED":
                    node.parent.color = "BLACK"
                    uncle.color = "BLACK"
                    node.parent.parent.color = "RED"
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self.left_rotate(node)
                    node.parent.color = "BLACK"
                    node.parent.parent.color = "RED"
                    self.right_rotate(node.parent.parent)
            else:
                uncle = node.parent.parent.left
                if uncle.color == "RED":
                    node.parent.color = "BLACK"
                    uncle.color = "BLACK"
                    node.parent.parent.color = "RED"
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self.right_rotate(node)
                    node.parent.color = "BLACK"
                    node.parent.parent.color = "RED"
                    self.left_rotate(node.parent.parent)

        self.root.color = "BLACK"

    def left_rotate(self, x):
        y = x.right
        x.right = y.left
        if y.left != self.NIL:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def right_rotate(self, x):
        y = x.left
        x.left = y.right
        if y.right != self.NIL:
            y.right.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x == x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y

    def search(self, song):
        return self._search_recursive(self.root, song)

    def _search_recursive(self, node, song):
        if node == self.NIL or node.song == song:
            if node == self.NIL:
                return None
            else:
                return node
        if song < node.song:
            return self._search_recursive(node.left, song)
        else:
            return self._search_recursive(node.right, song)

    # Delete a node from the Red-Black Tree
    def delete(self, song):
        node_to_delete = self.search(song)
        if node_to_delete is None:
            print(f"Song {song.title} not found in the tree.")
            return
        
        y = node_to_delete
        y_original_color = y.color
        if node_to_delete.left == self.NIL:
            x = node_to_delete.right
            self.transplant(node_to_delete, node_to_delete.right)
        elif node_to_delete.right == self.NIL:
            x = node_to_delete.left
            self.transplant(node_to_delete, node_to_delete.left)
        else:
            y = self.minimum(node_to_delete.right)
            y_original_color = y.color
            x = y.right
            if y.parent == node_to_delete:
                x.parent = y
            else:
                self.transplant(y, y.right)
                y.right = node_to_delete.right
                y.right.parent = y

            self.transplant(node_to_delete, y)
            y.left = node_to_delete.left
            y.left.parent = y
            y.color = node_to_delete.color

        if y_original_color == "BLACK":
            self.fix_delete(x)

    # Transplant the node being deleted with its replacement
    def transplant(self, u, v):
        if u.parent is None:
            self.root = v
        elif u == u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    # Fix the Red-Black Tree properties after deletion
    def fix_delete(self, x):
        while x != self.root and x.color == "BLACK":
            if x == x.parent.left:
                sibling = x.parent.right
                if sibling.color == "RED":
                    sibling.color = "BLACK"
                    x.parent.color = "RED"
                    self.left_rotate(x.parent)
                    sibling = x.parent.right

                if sibling.left.color == "BLACK" and sibling.right.color == "BLACK":
                    sibling.color = "RED"
                    x = x.parent
                else:
                    if sibling.right.color == "BLACK":
                        sibling.left.color = "BLACK"
                        sibling.color = "RED"
                        self.right_rotate(sibling)
                        sibling = x.parent.right

                    sibling.color = x.parent.color
                    x.parent.color = "BLACK"
                    sibling.right.color = "BLACK"
                    self.left_rotate(x.parent)
                    x = self.root
            else:
                sibling = x.parent.left
                if sibling.color == "RED":
                    sibling.color = "BLACK"
                    x.parent.color = "RED"
                    self.right_rotate(x.parent)
                    sibling = x.parent.left

                if sibling.right.color == "BLACK" and sibling.left.color == "BLACK":
                    sibling.color = "RED"
                    x = x.parent
                else:
                    if sibling.left.color == "BLACK":
                        sibling.right.color = "BLACK"
                        sibling.color = "RED"
                        self.left_rotate(sibling)
                        sibling = x.parent.left

                    sibling.color = x.parent.color
                    x.parent.color = "BLACK"
                    sibling.left.color = "BLACK"
                    self.right_rotate(x.parent)
                    x = self.root

        x.color = "BLACK"

    # Find the node with the minimum value (used for deletion)
    def minimum(self, node):
        while node.left != self.NIL:
            node = node.left
        return node


class  AVLNode:
    """
    The node class for the AVL tree.
    Source: https://www.datacamp.com/tutorial/avl-tree?dc_referrer=https%3A%2F%2Fwww.google.com%2F
    """
    def  __init__(self,  song,  parent  =  None):
        self.song  =  song
        self.parent  =  parent
        self.left  =  None
        self.right  =  None
        self.height  =  1

    def  left_height(self):
        #  Get  the  heigth  of  the  left  subtree
        return  0  if  self.left  is  None  else  self.left.height
    
    def  right_height(self):
        #  Get  the  height  of  the  right  subtree
        return  0  if  self.right  is  None  else  self.right.height
    
    def  balance_factor(self):
        #  Get  the  balance  factor
        return  self.left_height()  -  self.right_height()
    
    def  update_height(self):
        #  Update  the  heigth  of  this  node
        self.height  =  1  +  max(self.left_height(),self.right_height())
        
    def  set_left(self,  node):
        #  Set  the  left  child
        self.left  =  node
        if  node  is  not  None:
            node.parent  =  self
        self.update_height()
    
    def  set_right(self,  node):
        #  Set  the  right  child
        self.right  =  node
        if  node  is  not  None:
            node.parent  =  self
        self.update_height()

    def  is_left_child(self):
        #  Check  whether  this  node  is  a  left  child
        return  self.parent  is  not  None  and  self.parent.left  ==  self
    
    def  is_right_child(self):
        #  Check  whether  this  node  is  a  right  child
        return  self.parent  is  not  None  and  self.parent.right  ==  self

class  AVLTree:
    """
    The AVL tree class implemented based on:
    https://www.datacamp.com/tutorial/avl-tree?dc_referrer=https%3A%2F%2Fwww.google.com%2F
    """
    def  __init__(self):
        self.root  =  None
        self.size = 0

    def  rotate_left(self,  a):
        b  =  a.right
        #  1.  The  new  right  child  of  A  becomes  the  left  child  of  B
        a.set_right(b.left)
        #  2.  The  new  left  child  of  B  becomes  A
        b.set_left(a)
        return  b  #  3.  Return  B  to  replace  A  with  it
    
    def  rotate_right(self,  a):
        b  =  a.left
        a.set_left(b.right)
        b.set_right(a)
        return  b

    def  rebalance(self,  node):
        if  node  is  None:
            #  Empty  tree,  no  rebalancing  needed
            return  None
        balance  =  node.balance_factor()
        if  abs(balance)  <=  1:
            #  The  node  is  already  balanced,  no  rebalancing  needed
            return  node
        if  balance  ==  2:  
            #  Cases  1  and  2,  the  tree  is  leaning  to  the  left
            if  node.left.balance_factor()  ==  -1:  
                #  Case  2,  we  first  do  a  left  rotation
                node.set_left(self.rotate_left(node.left))
            return  self.rotate_right(node)
        #  Balance  must  be  -2
        #  Cases  3  and  4,  the  tree  is  leaning  to  the  left
        if  node.right.balance_factor()  ==  1:
            #  Case  4,  we  first  do  a  right  rotation
            node.set_right(self.rotate_right(node.right))  
        return  self.rotate_left(node)

    def  insert(self,  value):
        self.size  +=  1
        parent  =  None
        current  =  self.root
        while  current  is  not  None:
            parent  =  current
            if  value  <  current.song:
                #  Value  to  insert  is  smaller  than  node  value,  go  left
                current  =  current.left
            else:
                #  Value  to  insert  is  larger  than  node  value,  go  right
                current  =  current.right

        #  We  found  the  parent,  create  the  new  node
        new_node  =  AVLNode(value,  parent)
        #  Case  1:  The  parent  is  None  so  the  new  node  is  the  root
        if  parent  is  None:
            self.root  =  new_node
        else:
            #  Case  2:  Set  the  new  node  as  a  child  of  the  parent
            if  value  <  parent.song:
                parent.left  =  new_node
            else:
                parent.right  =  new_node
        #  After  a  new  node  is  added,  we  need  to  restore  balance
        self.restore_balance(new_node)

    def  restore_balance(self,  node):
        current  =  node
        #  Go  up  the  tree  and  rebalance  left  and  right  children
        while  current  is  not  None:
            current.set_left(self.rebalance(current.left))
            current.set_right(self.rebalance(current.right))
            current.update_height()
            current  =  current.parent
        self.root  =  self.rebalance(self.root)
        self.root.parent  =  None

    def  leftmost(self,  starting_node):
        #  Find  the  leftmost  node  from  a  given  starting  node
        previous  =  None
        current  =  starting_node
        while  current  is  not  None:
            previous  =  current
            current  =  current.left
        return  previous
    
    def  minimum(self):
        #  Return  the  minimum  value  in  the  tree
        if  self.root  is  None:
            raise  Exception("Empty  tree")
        return  self.leftmost(self.root).value

    def  rightmost(self,  starting_node):
        #  Find  the  rightmost  node  from  a  given  starting  node
        previous  =  None
        current  =  starting_node
        while  current  is  not  None:
            previous  =  current
            current  =  current.right
        return  previous
    
    def  maximum(self):
        #  Find  the  maximum  value  in  the  tree
        if  self.root  is  None:
            raise  Exception("Empty  tree")
        return  self.rightmost(self.root).value

    def  search(self,  song):
        #  Returns  the  node  containing  a  given  value  or  None  if  no
        #  such  node  exists
        current  =  self.root
        while  current  is  not  None:
            if  song  ==  current.song:
                return  current
            if  song  <  current.song:
                current  =  current.left
            else:
                current  =  current.right
        return  None

    def  __contains__(self,  value):
        node  =  self.search(value)
        return  node  is  not  None

    def  delete_leaf(self,  node):
        if  node.parent  is  None:
            self.root  =  None
        elif  node.is_left_child():
            node.parent.left  =  None
            node.parent  =  None
        else:
            node.parent.right  =  None
            node.parent  =  None

    def  delete(self,  value):
        #  Delete  a  value  from  the  tree
        node  =  self.search(value)
        if  node  is  None:
            raise  Exception("Value  not  stored  in  tree")

        replacement  =  None
        rebalance_node  =  node.parent
        if  node.left  is  not  None:
            #  There's  a  left  child  so  we  replace  with  rightmost  node
            replacement  =  self.rightmost(node.left)
            #  Check  if  reparenting  is  needed
            if  replacement.is_left_child():
                replacement.parent.set_left(replacement.left)
            else:
                replacement.parent.set_right(replacement.left)
        elif  node.right  is  not  None:
            #  There's  a  right  child  so  we  replace  with  the  leftmost  node
            replacement  =  self.leftmost(node.right)
            #  Check  if  reparenting  is  needed
            if  replacement.is_left_child():
                replacement.parent.set_left(replacement.right)
            else:
                replacement.parent.set_right(replacement.right)

        if  replacement:
            #  We  found  a  replacement  so  replace  the  value
            node.song  =  replacement.value
            rebalance_node  =  replacement.parent
        else:
            #  No  replacement  so  it  means  the  node  to  delete  is  a  leaf
            self.delete_leaf(node)
        if  rebalance_node  is  not  None:
            self.restore_balance(rebalance_node)

    def  search_lb_ub(self,  node,  lb,  ub,  results):
        #  Search  for  values  between  lower  bound  and  upper  bound
        if  node  is  None:
            return

        if  lb  <=  node.value  and  node.value  <=  ub:
            results.append(node.value)
        if  node.value  >=  lb:
            self.search(node.left,  lb,  ub,  results)
        if  node.value  <=  ub:
            self.search(node.right,  lb,  ub,  results)

    def  range_query(self,  lb,  ub):
        #  Search  for  values  between  lower  bound  and  upper  bound
        results  =  []
        self.search(self.root,  lb,  ub,  results)
        return  results

class MusicApp:
    """
    The Music App class manages all the functionality of the music App. 
    These include adding abd deleting playlists, adding and deleting songs in playlists,
    as well as saving and loading playlists. 
    It also offers to choose from 8 sorting algorithms and 6 search algorithms
    for lists. Additionally search can be performed in 3 different tree types.
    """
    def __init__(self, name=None):
        self.name = name
        self.playlists = dict()
        self.playlist_dir = "saved_playlists"
        os.makedirs(self.playlist_dir, exist_ok=True)
    
    def save_playlists(self):
        # Saves playlist and including songs to json file
        songs_str = jsonpickle.encode(self.playlists, unpicklable=False)
        fout = open(os.path.join(self.playlist_dir, self.name), "w")
        json_songs = json.loads(songs_str)
        for playlist_name in json_songs.keys():
            json_songs[playlist_name]["songs"] = None
            json_songs[playlist_name]["avl"] = None
            json_songs[playlist_name]["rbt"] = None
            json_songs[playlist_name]["bst"] = None
        json.dump(json_songs, fout, indent=4)
        fout.close()

    def load_playlists(self):
        # Loads playlist and including songs from json file and fills the 
        # data in playlist and song objects
        file_path = os.path.join(self.playlist_dir, self.name)
        if not os.path.isfile(file_path):
            print("This Playlist does not exist!")
            return -1
        
        json_songs = json.load(open(file_path))
        for playlist_name in json_songs.keys():
            playlist = Playlist(playlist_name)
            playlist.total_time = json_songs[playlist_name]["total_time"]
            playlist.songs = sorted([Song(**song) for song in json_songs[playlist_name]["songs_not_sorted"]])
            playlist.songs_not_sorted = [Song(**song) for song in json_songs[playlist_name]["songs_not_sorted"]]

            for song in np.random.permutation(playlist.songs):
                playlist.bst.insert(song)
                playlist.rbt.insert(song)
                playlist.avl.insert(song)
            self.playlists[playlist_name] = playlist

        print(f"{self.name} successfully loaded!")
        return 1

    def add_song(self, playlist_name, title, artist, album, genre, song_time):
        # Adds song to trees and lists of the selected playlist
        song = Song(title, artist, album, genre, song_time)
        playlist = self.playlists[playlist_name]
        playlist.songs_not_sorted.append(song)
        playlist.songs.append(song)
        playlist.songs.sort()  # Sorting for display and linear search
        playlist.bst.insert(song) 
        playlist.rbt.insert(song)
        playlist.avl.insert(song)
        playlist.total_time += song_time
        print(f"'{song}' added to your music library.")
        
    def add_random_songs(self, playlist_name, count):
        # Adds randomly generated songs to the selected playlist.
        # Possible genres are fetched from the Deezer API. Random artist names, 
        # song titles, and album names are generated with help of different libraries.
        playlist = self.playlists[playlist_name]

        for c in range(count):
            # Generate title of random length
            number_title_words = random.randint(1, 3)
            if number_title_words == 1:
                title = generate_slug(2).replace("-", " ").split(" ")[0]
            else:
                title = generate_slug(number_title_words).replace("-", " ")
            
            # Generate album of random length
            number_album_words = random.randint(1, 2)
            album = randomname.get_name().replace("-", " ")
            if number_album_words == 1:
                album = album.split(" ")[0]
            
            # Generate a random full name
            number_artist_words = random.randint(1, 2)
            artist = generate_name(style='capital') 
            if number_artist_words == 1: 
                artist = artist.split(" ")[0]

            # Genres from Deezer API fetchen
            genre_file = "genres.json"
            if not os.path.isfile(genre_file):
                url = "https://api.deezer.com/genre"
                response = requests.get(url)
                response = response.json()
                json.dump(response, open(genre_file, "w")) 

            response = json.load(open(genre_file))   
            genres = [genre["name"] for genre in response["data"]]
            genre = random.choice(genres)

            # Duration
            song_time = random.randint(10, 600)  # In seconds

            # Add the song 
            #self.add_song(playlist_name, title, artist, album, random_genre, seconds)

            song = Song(title, artist, album, genre, song_time)
            playlist.songs_not_sorted.append(song)
            playlist.songs.append(song)
            playlist.bst.insert(song) 
            playlist.rbt.insert(song)
            playlist.avl.insert(song)
            playlist.total_time += song_time
            if c % 100==0:
                print(f"{c} random songs generated.")
        print(f"{c} random songs added to your music library.")
        playlist.songs.sort()  # Sorting for display and linear search

    def delete_song(self, playlist_name, title):
        # Deletes the song from the selected playlist. 
        # For this it is first checked if the song is contained in the song list,
        # and afterwards it is removed from the song list and all trees.

        playlist = self.playlists[playlist_name]
        song_to_delete = next((s for s in playlist if s.title == title), None)
        if song_to_delete:
            song_time = playlist.songs[song_to_delete]
            playlist.total_time -= song_time
            playlist.songs_not_sorted.remove(song_to_delete)
            playlist.songs.remove(song_to_delete)
            playlist.bst = BinarySearchTree()  # Rebuild the binary search tree after deletion
            for s in playlist:
                playlist.bst.insert(s)
            print(f"'{song_to_delete}' removed from your music library.")
            playlist.avl.delete(Song(title, "", "", ""))
            playlist.rbt.delete(Song(title, "", "", ""))
        else:
            print(f"'{title}' not found in your music library.")

    def delete_playlist(self, playlist_name):
        # Deletes the selected playlist including all the songs from the music app.
        if playlist_name in self.playlists:
            self.playlists.pop(playlist_name)
            print(f"playlist {playlist_name} deleted")
        else: 
            print(f"playlist {playlist_name} does not exist.")

    def add_playlist(self, name):
        # Adds a new empty playlist with the selected name to the music app
        self.playlists[name] = Playlist(name)
        print(f"Created new playlist '{name}'.")

    def display_songs(self, playlist_name, sorted=True):
        # Shows all the songs in the selected playlist. 
        # It is possible to display the songs sorted or in the actual order.

        playlist = self.playlists[playlist_name]
        if playlist.songs:
            print("Your music library:")
            if sorted:
                for i, song in enumerate(playlist, 1):
                    print(f"{i}. {song}")
            else:
                for i, song in enumerate(playlist.songs_not_sorted, 1):
                    print(f"{i}. {song}")
        else:
            print("Your music library is empty.")

    def display_playlists(self):
        # Display information about all the playlists in the music app 
        # e.g. playlist name, playtime and number of contained songs 
        if self.playlists:
            print("Your music library:")
            for playlist in self.playlists.values():
                print(f"{playlist}")
        else:
            print("Empty playlists.")

    def shuffle_playlist(self, playlist_name):
        shuffled_songs = list(np.random.permutation(self.playlists[playlist_name].songs_not_sorted))
        self.playlists[playlist_name].songs_not_sorted = shuffled_songs


    #########################################
    # This section contains sort algorithms
    #########################################
    def merge_sort(self, songs):
        """
        Source: algorithm was taken from the lecture
        Sorts an array in ascending order using the merge sort algorithm.

        The merge sort algorithm follows a divide-and-conquer approach.
        It consists of three main steps: Divide, Conquer, and Merge.

        Steps:
        1. Divide: Split the array into two halves.
        2. Conquer: Recursively sort both halves.
        3. Merge: Merge the two sorted halves into a single sorted array.

        Time Complexity: O(n log n) for all cases (best, average, worst)
        """
        # If the array has one or no element, it is already sorted
        if len(songs) <= 1:
            return songs

        # Find the middle point to divide the array into two halves
        mid = len(songs) // 2

        # Call merge_sort recursively for both halves
        left_half = self.merge_sort(songs[:mid])
        right_half = self.merge_sort(songs[mid:])

        # Merge the two halves
        return self.merge(left_half, right_half)

    def merge(self, left, right):
        """
        Source: algorithm was taken from the lecture

        Merges two sorted lists into one sorted list.

        :param left: Sorted left half
        :param right: Sorted right half
        :return: Merged and sorted list

        The merging process involves:
        1. Initializing an empty list to store the merged elements.
        2. Using two pointers to track positions in the left and right lists.
        3. Comparing elements from both lists and appending the smaller element to the sorted list.
        4. If there are remaining elements in either list after the comparison, append them to the sorted list.
        """
        sorted_array = []
        i = j = 0

        # Traverse both lists and append the smaller element from either list to the sorted_array
        while i < len(left) and j < len(right):
            if left[i] < right[j]:
                sorted_array.append(left[i])
                i += 1
            else:
                sorted_array.append(right[j])
                j += 1

        # Append remaining elements of left and right lists
        sorted_array.extend(left[i:])
        sorted_array.extend(right[j:])

        return sorted_array

    
    def partition(self, songs, low, high):
        # Function to find the partition position needed for Quick sort
        # Source: https://www.geeksforgeeks.org/python-program-for-quick_sort/

        # choose the rightmost element as pivot
        pivot = songs[high]

        # pointer for greater element
        i = low - 1

        # traverse through all elements
        # compare each element with pivot
        for j in range(low, high):
            if songs[j] <= pivot:

                # If element smaller than pivot is found
                # swap it with the greater element pointed by i
                i = i + 1

                # Swapping element at i with element at j
                (songs[i], songs[j]) = (songs[j], songs[i])

        # Swap the pivot element with the greater element specified by i
        (songs[i + 1], songs[high]) = (songs[high], songs[i + 1])

        # Return the position from where partition is done
        return i + 1

    def quick_sort(self, songs, low=0, high=None):
        """
        Source: https://www.geeksforgeeks.org/python-program-for-quick_sort/
        Python program for implementation of quick sort

        This implementation utilizes pivot as the last element in the nums list
        It has a pointer to keep track of the elements smaller than the pivot
        At the very end of partition() function, the pointer is swapped with the pivot
        to come up with a "sorted" nums relative to the pivot

        Time Complexity: O(n log n) on average, but O(n^2) in the worst case (when the pivot selection is poor).
        """
        if high is None:
            high = len(songs)-1
        if low < high:

            # Find pivot element such that
            # element smaller than pivot are on the left
            # element greater than pivot are on the right
            pi = self.partition(songs, low, high)

            # Recursive call on the left of pivot
            self.quick_sort(songs, low, pi - 1)

            # Recursive call on the right of pivot
            self.quick_sort(songs, pi + 1, high)
        return songs

    def selection_sort(self, songs, size=None):
        """
        Source: https://www.geeksforgeeks.org/python-program-for-selection-sort/

        Sorts the list of songs using the Selection Sort algorithm.
        
        Selection Sort works by repeatedly finding the minimum element from the unsorted 
        part of the list and swapping it with the first unsorted element. This process 
        is repeated until the list is fully sorted.
        
        Time Complexity: O(n^2), where n is the number of songs.
        """
        if size == None:
            size = len(songs)
        for ind in range(size):
            min_index = ind

            for j in range(ind + 1, size):
                # select the minimum element in every iteration
                if songs[j] < songs[min_index]:
                    min_index = j
            # swapping the elements to sort the array
            (songs[ind], songs[min_index]) = (songs[min_index], songs[ind])
        return songs

    def insertion_sort(self, songs):
        """
        Quelle: https://www.geeksforgeeks.org/python-program-for-insertion-sort/
        Sorts the list of songs using the Insertion Sort algorithm.
        
        Insertion Sort builds the sorted list one item at a time by comparing each new element 
        to those already sorted. Elements are shifted to the right to make room for the new 
        element in its correct position.
        
        Time Complexity: O(n^2) in the worst case, O(n) in the best case (nearly sorted data).
        """
        n = len(songs) # Get the length of the array
        
        if n <= 1:
            return # If the array has 0 or 1 element, it is already sorted, so return

        for i in range(1, n): # Iterate over the array starting from the second element
            key = songs[i] # Store the current element as the key to be inserted in the right position
            j = i-1
            while j >= 0 and key < songs[j]: # Move elements greater than key one position ahead
                songs[j+1] = songs[j] # Shift elements to the right
                j -= 1
            songs[j+1] = key # Insert the key in the correct position
        return songs

    def shell_sort(self, songs):
        """
        Source: https://www.geeksforgeeks.org/python-program-for-shellsort/
        Sorts the list of songs using the Shell Sort algorithm.
        
        Shell Sort is a generalization of Insertion Sort that allows the exchange 
        of elements that are far apart by using a diminishing gap sequence.
        
        Time Complexity: O(n^2) in the worst case, but O(n log n) with good gap sequences.
        """

        # Start with a big gap, then reduce the gap
        n = len(songs)
        gap = n//2

        # Do a gapped insertion sort for this gap size.
        # The first gap elements a[0..gap-1] are already in gapped
        # order keep adding one more element until the entire array
        # is gap sorted
        while gap > 0:
            for i in range(gap,n):

                # add a[i] to the elements that have been gap sorted
                # save a[i] in temp and make a hole at position i
                temp = songs[i]

                # shift earlier gap-sorted elements up until the correct
                # location for a[i] is found
                j = i
                while j >= gap and songs[j-gap] >temp:
                    songs[j] = songs[j-gap]
                    j -= gap

                # put temp (the original a[i]) in its correct location
                songs[j] = temp
            gap //= 2
        return songs

    def bubble_sort(self, songs):
        """
        Source: Lecture
        Sorts the list of songs using the Bubble Sort algorithm.
        
        Bubble Sort repeatedly steps through the list, compares adjacent elements, and 
        swaps them if they are in the wrong order. 
        
        Time Complexity: O(n^2) in all cases.
        """
        n = len(songs)
        # Traverse through all elements in the array
        for i in range(n-1):
            # Last i elements are already sorted, so inner loop will only consider unsorted part
            for j in range(0, n-i-1):
                # If current element is greater than next one, swap both of them.
                if songs[j] > songs[j+1]:
                    songs[j], songs[j+1] = songs[j+1], songs[j]
        return songs

    def optimized_bubble_sort(self, songs):
        """
        Source: lecture

        Sorts the list of songs using an optimized version of the Bubble Sort algorithm.
        
        This optimization includes a flag (`swapped`) that stops the algorithm early 
        if no elements were swapped during an iteration, indicating the list is already sorted.
        
        Time Complexity: O(n^2) in the worst case, but O(n) in the best case (already sorted list).
        """
        n = len(songs)
        for i in range(n - 1):
            swapped = False
            # Last i elements are already sorted, so inner loop will only consider unsorted part
            for j in range(0, n - i - 1):
                if songs[j] > songs[j + 1]:
                    songs[j], songs[j + 1] = songs[j + 1], songs[j]
                    swapped = True

            # If no two elements were swapped in the inner loop, then the array is sorted
            if not swapped:
                break
        return songs

    def cocktail_sort(self, songs):
        """
        Source https://www.geeksforgeeks.org/python-program-for-cocktail-sort/
        
        Sorts the list of songs using the Cocktail Shaker Sort algorithm.
        
        Cocktail Shaker Sort is a variation of Bubble Sort. It passes through 
        the list in both directions alternately, moving large elements to the 
        end and small elements to the beginning.
        
        Time Complexity: O(n^2), but it can finish earlier than Bubble Sort 
        when elements are partially sorted.
        """
        n = len(songs)
        swapped = True
        start = 0
        end = n-1
        while (swapped==True):

            # reset the swapped flag on entering the loop,
            # because it might be true from a previous
            # iteration.
            swapped = False

            # loop from left to right same as the bubble
            # sort
            for i in range (start, end):
                if (songs[i] > songs[i+1]) :
                    songs[i], songs[i+1]= songs[i+1], songs[i]
                    swapped=True

            # if nothing moved, then array is sorted.
            if (swapped==False):
                break

            # otherwise, reset the swapped flag so that it
            # can be used in the next stage
            swapped = False

            # move the end point back by one, because
            # item at the end is in its rightful spot
            end = end-1

            # from right to left, doing the same
            # comparison as in the previous stage
            for i in range(end-1, start-1,-1):
                if (songs[i] > songs[i+1]):
                    songs[i], songs[i+1] = songs[i+1], songs[i]
                    swapped = True

            # increase the starting point, because
            # the last stage would have moved the next
            # smallest number to its rightful spot.
            start = start+1
        return songs

    def sort_playlist(self, playlist_name):
        # Function to enable choosing a sorting algorithm for the playlist
        songs = self.playlists[playlist_name].songs_not_sorted

        message = (f"Choose search method:\n"
                   f"1. Merge sort\n"
                   f"2. Quick sort\n"
                   f"3. Selection sort\n"
                   f"4. Insertion sort\n"
                   f"5. Shell sort\n"
                   f"6. Bubble sort\n"
                   f"7. Optimized bubble sort\n"  
                   f"8. Cocktail shaker sort\n"  
                   ) 
        sort_method = None
        if not sort_method:
            sort_method = input(message).strip().lower()

        key = input("Do you want to sort by (T)itle, (A)rtist, (AL)bum (G)enre or (P)laytime?").lower().strip()
        key_dict = {"t":"title", "a": "artist", "al": "album", "g":"genre", "p":"playtime"}
        if key not in key_dict:
            print("Invalid input.")
            return -1
        key = key_dict[key]
        # If not sorting by title change the key for song comparison
        if key!= "title":
            for song in songs:
                song.set_key(key)

        start_time = time.time()    
        if sort_method == '1':      
            result = self.merge_sort(songs)
        elif sort_method == '2':
            result = self.quick_sort(songs)
        elif sort_method == '3':
            result = self.selection_sort(songs)
        elif sort_method == '4':
            result = self.insertion_sort(songs)
        elif sort_method == '5':
            result = self.shell_sort(songs)
        elif sort_method == '6':
            result = self.bubble_sort(songs)
        elif sort_method == '7':
            result = self.optimized_bubble_sort(songs)
        elif sort_method == '8':
            result = self.cocktail_sort(songs)
        else:
            print("Invalid sort method selected.")
            sort_method = None
            return -1
        end_time = time.time()

        print("Playlist successfully sorted")
        # If set sortkey again to "title" for higher consistency
        if key!= "title":
            for song in result:
                song.set_key("title")
        self.playlists[playlist_name].songs_not_sorted = list(result)          
        # Print needed time
        needed_time = end_time - start_time
        print(f"Runtime: {needed_time:.2f} seconds")
     

    ##########################################
    # This section contains search algorithms
    ##########################################
    def search_with_binary_tree(self, playlist_name, title):
        """
        Searches for a song by title in a playlist using a Binary Search Tree (BST).

        A Binary Search Tree is a tree data structure where each node has at most two children, 
        and the left child is smaller than the node, while the right child is larger.
        This method searches for a song by comparing the song titles recursively.

        Time Complexity: O(h), where h is the height of the tree. In the average case, 
        this is O(log n), but in the worst case (unbalanced tree), it can degrade to O(n).
        """
        song_to_search = Song(title, "", "", "")
        return self.playlists[playlist_name].bst.search(song_to_search)

    def search_with_red_black_tree(self, playlist_name, title):
        """
        Searches for a song by title in a playlist using a Red-Black Tree.

        A Red-Black Tree is a self-balancing binary search tree where each node stores 
        an extra bit representing "color" (red or black). This ensures the tree remains balanced, 
        providing efficient searching, insertion, and deletion operations.

        Time Complexity: O(log n), since Red-Black Trees maintain balanced structure.
        """
        song_to_search = Song(title, "", "", "")
        return self.playlists[playlist_name].rbt.search(song_to_search)

    def search_with_avl_tree(self, playlist_name, title):
        """
        Searches for a song by title in a playlist using an AVL Tree.

        An AVL Tree is a self-balancing binary search tree where the heights of the 
        left and right subtrees of any node differ by no more than one. If at any time 
        they differ by more than one, rebalancing operations are performed to restore balance.

        Time Complexity: O(log n), since AVL Trees maintain a balanced height at all times.
        """
        song_to_search = Song(title, "", "", "")
        return self.playlists[playlist_name].avl.search(song_to_search)    

    def bfs(self, title, root=None):
        song = Song(title, "", "", "")
        """
        Code adapted from: https://csanim.com/tutorials/breadth-first-search-python-visualization-and-code
        Breadth-First Search (BFS) algorithm for searching a song by title in a binary tree.

        BFS explores the tree level by level, starting from the root node and expanding 
        outward. It uses a queue data structure to traverse the tree, adding child nodes 
        of the current node before moving to the next node.

        Time Complexity: O(n), where n is the number of nodes in the tree, since 
        each node is visited exactly once.

        Space Complexity: O(w), where w is the maximum width of the tree (the maximum 
        number of nodes at any level).
        
        """
        if root is None:
            return
        queue = [root]

        while len(queue) > 0:
            cur_node = queue.pop(0)
            if cur_node.song == song: 
                return cur_node

            if cur_node.left is not None:
                queue.append(cur_node.left)

            if cur_node.right is not None:
                queue.append(cur_node.right)
        return None

    def dfs(self, title, tree):
        """
        Source: https://llego.dev/posts/implementing-depth-first-search-python-traverse-binary-tree/
        Depth-First Search (DFS) algorithm for searching a song by title in a binary tree.
        It relies on the depth first search iterator implemented in the tree class, to traverse all nodes.
        
        DFS explores the tree by going as deep as possible along each branch before backtracking. 
        This implementation uses a pre-order traversal (visiting the current node before 
        its children).

        Time Complexity: O(n), where n is the number of nodes in the tree, as each node 
        is visited once.

        Space Complexity: O(h), where h is the height of the tree (due to recursion or 
        stack storage).
        """
        for node in tree:
            if node and node.song == Song(title, "", "", ""):
                return node
        return None  

    def linear_search(self, songs, song_to_find):
        """
        Source: lecture 
        Linear search algorithm for finding a song by title in a playlist.

        This method iterates through the playlist from the beginning to the end,
        comparing each song's title with the search query. It stops as soon as a 
        matching title is found.

        Time Complexity: O(n), where n is the number of songs in the playlist, 
        because it might have to check every song.

        Space Complexity: O(1), since no additional memory is used except for a 
        few variables.
        """  
        for index, song in enumerate(songs):
            if song == song_to_find:
                return index
        return -1

    def linear_search_find_all_elements(self, songs, song_to_find):
        """
        Modification of linear search to return indices of all the searched elements
        """  
        indices = []
        for index, song in enumerate(songs):
            if song == song_to_find:
                indices.append(index)
            elif song > song_to_find:
                break
        return indices  # Return the list of indices
  
    def binary_search(self, songs, song_to_find, low=0, high=None):
        """
        Source: lecture
        Binary search algorithm for finding a song by title in a sorted playlist.

        This method works by repeatedly dividing the search interval in half. It 
        assumes the playlist is sorted by song titles. The algorithm compares the 
        middle element with the target title and narrows the search range accordingly.

        Time Complexity: O(log n), where n is the number of songs, since it divides 
        the search range by half at each step.

        Space Complexity: O(log n), due to the recursive calls
        """

        if not high:
            high = len(songs) - 1
        if low > high:
            return -1  # Base case: target not found
        mid = (low + high) // 2
        
        if songs[mid] == song_to_find:
            return mid  # Base case: target found
        elif songs[mid] < song_to_find:
            return self.binary_search(songs, song_to_find, mid + 1, high)  # Search the right half
        else:
            return self.binary_search(songs, song_to_find, low, mid - 1)  # Search the left half

    def ternary_search(self, songs,  song_to_find, l=0, r=None):
        """
        Quelle: https://www.geeksforgeeks.org/ternary-search/
        Code was translated from Java to Python with help of ChatGPT
        
        Ternary Search algorithm for finding a song by title in a sorted playlist.

        Ternary search works by dividing the array into three equal parts and narrowing 
        the search region based on comparisons with the midpoints. It is a divide-and-conquer 
        algorithm similar to binary search, but it divides the array into three parts instead of two.

        Time Complexity: O(log₃ n), where n is the number of songs in the playlist.

        Space Complexity: O(log₃ n), due to the recursive calls made during the search.
        """
        if not r:
            r = len(songs)-1
        if r >= l:
            # Find the mid1 and mid2
            mid1 = l + (r - l) // 3
            mid2 = r - (r - l) // 3
            # Check if key is present at any mid
            if songs[mid1] == song_to_find:
                return mid1
            if songs[mid2] == song_to_find:
                return mid2

            # Since key is not present at mid,
            # check in which region it is present
            # then repeat the Search operation
            # in that region
            if song_to_find < songs[mid1]:
                # The key lies in between l and mid1
                return self.ternary_search(songs, song_to_find, l, mid1 - 1)
            elif song_to_find > songs[mid2]:
                # The key lies in between mid2 and r
                return self.ternary_search(songs, song_to_find, mid2 + 1, r)
            else:
                # The key lies in between mid1 and mid2
                return self.ternary_search(songs, song_to_find, mid1 + 1, mid2 - 1)
        
        # Key not found
        return -1

    def jump_search(self, songs, song_to_find):
        """
        Source: lecture
        Jump search algorithm for finding a song by title in a sorted playlist.

        Jump search works by dividing the playlist into blocks and jumping over the blocks 
        by a fixed step size (the square root of the total number of elements). Once a block 
        is found where the target song might reside, it performs a linear search within that block.

        Time Complexity: O(√n), where n is the number of songs in the playlist.

        Space Complexity: O(1), as no extra space is used except for variables.
        """
        n = len(songs)
        
        # Finding the optimal jump step
        step = int(n ** 0.5)
        prev = 0
        
        # Jump in blocks until the song at `step` is larger than or equal to the target
        while prev < n and songs[min(step, n) - 1] < song_to_find:
            prev = step
            step += int(n ** 0.5)
            if prev >= n:  # If we've jumped beyond the list
                return -1

        # Linear search within the block
        while prev < min(step, n) and songs[prev] < song_to_find:
            prev += 1

        # Check if we've found the song
        if prev < n and songs[prev] == song_to_find:
            return prev
        return -1

    def exponential_search(self, songs, song_to_find):
        """
        Source: lecture
        
        Exponential search algorithm for finding a song by title in a sorted playlist.

        Exponential search starts by checking increasingly larger intervals (doubling in size each time). 
        Once the range where the target song could be is identified, it performs a binary search 
        within that range.

        Time Complexity: O(log i), where i is the position of the target song. The doubling process 
        takes O(log i) comparisons, and the binary search takes O(log i) time as well.

        Space Complexity: O(log i), due to the recursive calls in the binary search.
        """
        if songs[0] == song_to_find:
            return 0

        pos = 1
        while pos < len(songs) and songs[pos] <= song_to_find:
            pos *= 2
 
        low, high = max(0, pos//2), min(pos, len(songs)-1)
        
        return self.binary_search(songs, song_to_find, low, high) 

    def fibonaccianSearch(self, songs, song_to_find, n=None): 
        """
        Source: https://www.geeksforgeeks.org/fibonacci-search-in-python/
        
        Fibonacci Search algorithm for finding a song by title in a sorted playlist.

        Fibonacci search divides the array into sections based on Fibonacci numbers and uses 
        a divide-and-conquer approach similar to binary search. It attempts to find the target 
        by narrowing the search range using the Fibonacci sequence.

        Time Complexity: O(log n), where n is the number of songs in the playlist.
        
        Space Complexity: O(1), as no additional space is used beyond a few variables.
        """
        if not n:
            n = len(songs)
        # Initialize fibonacci numbers
        fibMMm2 = 0  # (m-2)'th Fibonacci No.
        fibMMm1 = 1  # (m-1)'th Fibonacci No.
        fibM = fibMMm2 + fibMMm1  # m'th Fibonacci

        # fibM is going to store the smallest
        # Fibonacci Number greater than or equal to n
        while (fibM < n):
            fibMMm2 = fibMMm1
            fibMMm1 = fibM
            fibM = fibMMm2 + fibMMm1

        # Marks the eliminated range from front
        offset = -1

        # while there are elements to be inspected.
        # Note that we compare arr[fibMm2] with x.
        # When fibM becomes 1, fibMm2 becomes 0
        while (fibM > 1):

            # Check if fibMm2 is a valid location
            i = min(offset+fibMMm2, n-1)

            # If x is greater than the value at
            # index fibMm2, cut the subarray array
            # from offset to i
            if (songs[i] < song_to_find):
                fibM = fibMMm1
                fibMMm1 = fibMMm2
                fibMMm2 = fibM - fibMMm1
                offset = i

            # If x is less than the value at
            # index fibMm2, cut the subarray
            # after i+1
            elif (songs[i] > song_to_find):
                fibM = fibMMm2
                fibMMm1 = fibMMm1 - fibMMm2
                fibMMm2 = fibM - fibMMm1

            # element found. return index
            else:
                return i

        # comparing the last element with x */
        if(fibMMm1 and songs[n-1] == song_to_find):
            return n-1

        # element not found. return -1
        return -1

    def search_song(self, playlist_name, search_method=None):
        # Offers options to search for a song either using a seach tree or a list
        print("Search for a song:")
        if not search_method:
            search_method = input("Do you want to do (T)ree based search or (L)ist based search? ").strip().lower()
        if search_method == "t":
            self.tree_based_search(playlist_name)
        elif search_method == "l":
            self.list_based_search(playlist_name)
        else: 
            print("Invalid selection only (T)ree based and (L)ist based search are possible. Please enter 'T' or 'L'")
            search_method = None
    
    def tree_based_search(self, playlist_name, search_method=None, title=None):
        # Offers to search a song using different search tree types
        message = (f"Choose search method:\n"
                   f"1. Avl tree\n"
                   f"2. Binary search tree\n"
                   f"3. Red Black tree\n"
                   f"4. BFS in binary search tree\n"
                   f"5. DFS in binary search tree\n"
                   f"Enter your selection: ")
        
        if not search_method or not title:
            search_method = input(message).strip().lower()
            title = input("Enter song title: ").strip()
        start_time = time.time()    
        if search_method == '1':
            node = self.search_with_avl_tree(playlist_name, title)
        elif search_method == '2':
            node = self.search_with_binary_tree(playlist_name, title)
        elif search_method == '3':
            node = self.search_with_red_black_tree(playlist_name, title)
        elif search_method == '4':
            node = self.bfs(title, self.playlists[playlist_name].bst.get_root())
        elif search_method == '5':
            node = self.dfs(title, self.playlists[playlist_name].bst)
        else:
            print("Invalid search method selected.")
            search_method = None
            title = None
            return -1
        
        if node:
            print(f"'{title}' found in your music library.")
        else:
            print(f"'{title}' not found in your music library.")

        # Print runtime
        end_time = time.time()
        needed_time = end_time - start_time
        print(f"Runtime: {needed_time:.5f} seconds")

    def list_based_search(self, playlist_name, search_method=None, title=None):
        # Offer different algorithms to search in a (sorted) list
        message = (f"Choose search method:\n"
                   f"1. Linear search\n"
                   f"2. Binary search\n"
                   f"3. Ternary search\n"
                   f"4. Jump search\n"
                   f"5. Exponential search\n"
                   f"6. Fibonnaci search\n"  
                   f"7. Find all occurences (modified linear search)\n"
                   f"Enter your choice: "  ) 
        
        key = input("Do you want to search for (T)itle, (A)rtist, (AL)bum or (G)enre? ").lower().strip()
        key_dict = {"t":"title", "a": "artist", "al": "album", "g":"genre", "p":"playtime"}
        if key not in key_dict:
            print("Invalid input.")
            return -1
        key = key_dict[key]
        # If not searching by title change the key for song comparison 
        # and sort the list with quick_sort
        if key!= "title":
            songs = copy.deepcopy(self.playlists[playlist_name].songs)
            for song in songs:
                song.set_key(key)
            songs = self.quick_sort(songs)
        else:         
            songs = self.playlists[playlist_name].songs
                
        if not search_method or not title:
            search_method = input(message).strip().lower()
            search_value = input(f"Enter {key} of song you want to find: ").strip()
        
        song_to_find = Song("", "", "", "", key=key)
        setattr(song_to_find, key, search_value)
        start_time = time.time()    
        if search_method == '1':      
            result = self.linear_search(songs, song_to_find)
        elif search_method == '2':
            result = self.binary_search(songs, song_to_find)
        elif search_method == '3':
            result = self.ternary_search(songs, song_to_find)
        elif search_method == '4':
            result = self.jump_search(songs, song_to_find)
        elif search_method == '5':
            result = self.exponential_search(songs, song_to_find)
        elif search_method == '6':
            result = self.fibonaccianSearch(songs, song_to_find)
        elif search_method == '7':
            result = self.linear_search_find_all_elements(songs, song_to_find)
           
        else:
            print("Invalid search method selected.")
            search_method = None
            title = None
            return -1
        end_time = time.time()
        
        if search_method != "7" and result != -1:
            print(f"'{songs[result]}' found in your music library at position {result + 1}.")
        elif search_method == "7" and len(result)>0:
            print(f"Found {len(result)} results in your music library:")
            for r in result:
                print(songs[r])
        else:
            print(f"'{search_value}' not found in your music library.")
           
        # Print run time
        needed_time = end_time - start_time
        print(f"Runtime: {needed_time:.5f} seconds.")

def main():
    # Main functionality of the music app
    successful_initiated = False
    while not successful_initiated:
        choice = input("Do you want to create (N)ew playlist collection or (L)oad an existing one? ").strip().lower()
        if choice == "n":
            name = input("Please enter a name for the playlist collection: ").strip()
            app = MusicApp(name)
            successful_initiated = True
        elif choice == "l":
            name = input("Please enter the name of the playlist collection you want to load: ").strip()
            app = MusicApp(name)
            load_success = app.load_playlists()
            print(load_success)
            if load_success == 1:
                successful_initiated = True
        else: 
            "Input was invalid. It should be 'N' or 'L'"


    while True:
        print("\n------ Main Menu ------")
        print("1. Choose existing playlist")
        print("2. Delete existing playlist")
        print("3. Create new playlist")
        print("4. Show playlist overview")
        print("5. Save and Exit")
        print("6. Exit (without saving)")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            if not app.playlists:
                print("No playlists available. Please create one.")
                continue

            print("Please choose one of the following playlists:")
            for playlist_name in app.playlists.keys():
                print(playlist_name)
            playlist_name = input("Enter your choice: ").strip()

            if playlist_name in app.playlists:
                playlist_menu(app, playlist_name)
            else:
                print(f"Playlist '{playlist_name}' does not exist.")

        elif choice == '2':
            name = input("Enter the name of the playlist to delete: ").strip()
            app.delete_playlist(name)

        elif choice == '3':
            name = input("Enter the name of the new playlist: ").strip()
            app.add_playlist(name)
            playlist_menu(app, name)

        elif choice == '4':
            app.display_playlists()

        elif choice == '5':
            app.save_playlists()
            print(f"Playlist collection '{app.name}' was saved")
            print("Exiting Music App. Goodbye!")
            break
        elif choice == '6':
            print("Exiting Music App. Goodbye!")
            break
        else:
            print("Invalid choice. Please select again.")


def playlist_menu(app, playlist_name):
    # The playlist menu
    while True:
        print(f"\n--- Playlist '{playlist_name}' ---")
        print("1. Add Song")
        print("2. Delete Song")
        print("3. Display Songs")
        print("4. Shuffle Playlist")
        print("5. Sort Playlist")
        print("6. Search Song")
        print("7. Print Memory of Playlist")
        print("8. Back to Main Menu")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            second_choice = input("Do you want to add (O)ne specific song or (M)ultiple random songs? ").strip().lower()
            if second_choice == "o":
                title = input("Enter song title: ").strip()
                artist = input("Enter artist name: ").strip()
                album = input("Enter album name: ").strip()
                genre = input("Enter genre: ").strip()
                seconds = input("Enter length of the song in seconds: ").strip()
                if seconds.isdigit():
                    app.add_song(playlist_name, title, artist, album, genre, int(seconds))
                else:
                    print("Lenght of the song has to be a number")
            elif second_choice == "m":
                count = input("Enter the number of random songs to add: ").strip()
                if count.isdigit():
                    count = int(count)
                    app.add_random_songs(playlist_name, count)
                else:
                    print("Number of songs must be a number.")
            else:
                print("Invalid input.")

        elif choice == '2':
            title = input("Enter song title to delete: ").strip()
            app.delete_song(playlist_name, title)

        elif choice == '3':
            choice2 = input("Do you want to see (S)orted playlist or (A)ctual playlist order? ").strip().lower()
            if choice2 == "s":
                app.display_songs(playlist_name, sorted=True)
            elif choice2 == "a":
                app.display_songs(playlist_name, sorted=False)
            else:
                print("Invalid input. It should be 's' or 'u'.")

        elif choice == '4':
            app.shuffle_playlist(playlist_name)

        elif choice == '5':
            app.sort_playlist(playlist_name)

        elif choice == '6':
            app.search_song(playlist_name)

        elif choice == '7':
            app.playlists[playlist_name].memory_usage()

        elif choice == '8':
            break

        else:
            print("Invalid choice. Please select again.")
    
if __name__ == "__main__":
    main()
