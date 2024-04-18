import React from 'react';
import { ReactComponent as ArrowIconRight } from '../../icons/ArrowRightPopUp.svg'
import { ArrowProps } from './ArrowsTypes';

const RightArrow: React.FC<ArrowProps> = ({ onClick, className }) => (
  <button onClick={onClick} className={className}>
    <div className="div">
      <p className={'font-aeonik text-[16px] text-black bg-opacity-60'}>
        Next
      </p>
    </div>
    <ArrowIconRight />
  </button>
);

export default RightArrow;
