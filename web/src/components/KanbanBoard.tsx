import React, { useState } from 'react';
import './KanbanBoard.css';

function KanbanBoard() {
  return (
    <div className="board">
      <div className="boardColumn">
        <h3>Backlog</h3>
      </div>
      <div className="boardColumn">
        <h3>In Progress</h3>
      </div>
      <div className="boardColumn">
        <h3>Done</h3>
      </div>
    </div>
  );
}

export default KanbanBoard;
