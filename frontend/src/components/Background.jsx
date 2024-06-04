import React from 'react';
import Chatbot from './Chatbot';
import robot from '../assets/robot.gif'; // Import the anime1.gif image

const Background = () => {
  return (
    <div className="h-screen w-screen bg-gradient-to-r from-purple-900 via-gray-900 to-black flex items-center justify-center">
      <div className="absolute left-16 top-24 h-1/4 w-1/4 bg-cover bg-center mr-28 mt-10" style={{ backgroundImage: `url(${robot})`, maxWidth: '180px', maxHeight: '150px' }}></div>
      <div className="text-white text-center mt-5 ml-28">
        <h1 className="text-3xl font-bold mb-2">Explore New Schemes</h1>
        <p className="text-lg">Discover and select from a variety of schemes tailored just for you!</p>
      </div>
      <Chatbot />
    </div>
  );
};

export default Background;

