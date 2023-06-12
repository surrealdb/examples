import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';  // Import the CSS file
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons';
import { faPen } from '@fortawesome/free-solid-svg-icons';
import { ReactComponent as Title } from './assets/Stickies.svg';  // Import your SVG
import { ReactComponent as FooterImage } from './assets/dark.svg';  // replace './assets/FooterImage.svg' with the path to your SVG file



function App() {
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isAddingNote, setIsAddingNote] = useState(false);  // New piece of state

  useEffect(() => {
    const fetchNotes = async () => {
      const { data } = await axios.get('http://localhost:3001/notes');
      setNotes(data);
    };

    fetchNotes();
  }, []);

  const addNote = async () => {
    const note = { title, content };
    const { data } = await axios.post('http://localhost:3001/notes', note);
    setNotes(oldNotes => [...oldNotes, data]);
    setTitle('');
    setContent('');
    setIsAddingNote(false);  // Hide inputs after adding note
  };

  const handleDelete = async (id) => {
    const { data } = await axios.delete(`http://localhost:3001/api/notes/${id}`);
    if (data.message === "Note deleted successfully") {
      setNotes(notes.filter(note => note.id !== id));
    } else {
      console.error("Failed to delete note.");
    }
};

const [editingNote, setEditingNote] = useState(null);



const handleUpdate = async () => {
    const note = { title, content };
    const { data } = await axios.put(`http://localhost:3001/api/notes/${editingNote.id}`, note);
    setNotes(oldNotes => oldNotes.map(n => n.id === editingNote.id ? data : n));
    setTitle('');
    setContent('');
    setIsAddingNote(false);
    setEditingNote(null);  // Exit editing mode
  };



   return (
    <div className="container">
    <div>
    <Title className="title-svg" /> {/* Use SVG as a component */}
</div>
<div>
    <button className="addButton" onClick={() => {setIsAddingNote(true); setEditingNote(null);}}>+</button>
</div>
        {isAddingNote && (
            <>
                <input 
                    type="text" 
                    value={title} 
                    onChange={e => setTitle(e.target.value)} 
                    placeholder="Title" 
                />
                <textarea 
                    value={content} 
                    onChange={e => setContent(e.target.value)} 
                    placeholder="Note"
                />
                <button onClick={editingNote ? handleUpdate : addNote}>
                    {editingNote ? "Update Note" : "Submit Note"}
                </button>
            </>
        )}
        <div className="notesGrid"> {/* Wrap your notes with this div */}
            {notes.map(note => (
                <div key={note.id} className="note">
                    <h2 className="title" style={{ color: '#ff00a0' }}>{note.title}</h2>
                    <p>{note.content}</p>
                    <button onClick={() => handleDelete(note.id)}>
                        <FontAwesomeIcon icon={faTrash} />
                    </button>
                    <button onClick={() => {setEditingNote(note); setTitle(note.title); setContent(note.content); setIsAddingNote(true);}}>
                        <FontAwesomeIcon icon={faPen} />
                    </button>
                </div>
            ))}
        </div>
        <FooterImage className="dark-svg" />
    </div>

  );
}
export default App;