import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './customScrollbar.css'; // Add this line to import custom scrollbar styles

function Chatbot() {
  const [userInput, setUserInput] = useState('');
  const [chatlog, setChatlog] = useState([]);
  const [isChatting, setIsChatting] = useState(false);
  const chatContainerRef = useRef(null);

  const handleSubmit = async () => {
    if (userInput.trim() !== '') {
      const newChatlog = [...chatlog, { sender: 'user', message: userInput }];
      setChatlog(newChatlog);
      setUserInput('');
      setIsChatting(true); // Open animation box to full height immediately when the user submits input
  
      try {
        const response = await axios.post('http://127.0.0.1:5000/get_response', {
          user_input: userInput,
        });
  
        // Function to reveal the entire message with typing effect
        const revealMessage = async (message) => {
          let typedMessage = '';
          for (let i = 0; i <= message.length; i++) {
            typedMessage = message.substring(0, i);
            setChatlog((prevChatlog) => [...newChatlog, { sender: 'bot', message: typedMessage }]);
            await new Promise(resolve => setTimeout(resolve, 2)); // Adjust typing speed here (e.g.,  milliseconds)
          }
          setIsChatting(true);
        };
  
        // Call the function to reveal the message with typing effect
        await revealMessage(response.data.response);
      } catch (error) {
        setChatlog([...newChatlog, { sender: 'bot', message: 'Sorry, there was an error processing your request.' }]);
        setIsChatting(true);
      }
    }
  };
  
  
  
  

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatlog]);

  const renderMessage = (entry, index) => {
    return (
      <div key={index} className={`mb-4 p-3 rounded-lg ${entry.sender === 'user' ? 'bg-gray-300 text-gray-800 self-end' : 'bg-gray-800 text-white self-start'}`}>
        <div dangerouslySetInnerHTML={{ __html: entry.message }} />
      </div>
    );
  };

  return (
    <div className="h-screen w-screen overflow-hidden flex items-center justify-center">
      <div className={`transition-all duration-500 transform ${isChatting ? 'h-full w-3/5 translate-x-1/4' : 'h-1/3 w-1/3'} bg-opacity-10 backdrop-blur-lg rounded-lg shadow-xl overflow-hidden relative z-10 flex items-center justify-center bg-gray-100 text-gray-800`} style={{ width: '520px' }}>
        <div className="h-full flex flex-col bg-gradient-to-r from-purple-700 to-indigo-900 w-full">
          <div className="flex-1 p-4 overflow-y-auto custom-scrollbar" ref={chatContainerRef}>
            {chatlog.length === 0 && !isChatting ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <p className="text-2xl mb-4">Navigate the world of schemes</p>
              </div>
            ) : (
              chatlog.map(renderMessage)
            )}
          </div>
          <div className="flex items-center gap-2 p-4 border-t border-gray-700 button-container">
            <input
              type="text"
              id="userInput"
              placeholder={isChatting ? '' : "Type your message here..."}
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSubmit();
                }
              }}
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none bg-gray-100 text-gray-800"
            />
            <button
              id="sendBtn"
              onClick={handleSubmit}
              className="px-4 py-2 bg-purple-700 text-white rounded-lg hover:bg-purple-800 focus:outline-none transition duration-300"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chatbot;
