// CommonContext.js
import React, { FC, createContext, useContext } from 'react';
import { Link } from 'react-router-dom';
import { ReactComponent as LogoIcon } from '../../icons/logo.svg'

const CommonContext = createContext<React.ReactNode | null>(null);
type CommonProviderProps = {
    children?: React.ReactNode
}

export const CommonProvider: FC<CommonProviderProps> = ({ children }) => {
  const commonElement = (
    <div className={'text-center justify-between flex p-6 border-b-[1px] border-[#E5E6E4]'}>
      <LogoIcon />
      <div className={'flex flex-row gap-8'}>
        <Link to="/Chat">
          <button>
            <p className={'font-aeonikBold text-[16px] leading-5 hover:text-[#006F33]'}>
              Chat
            </p>
          </button>
        </Link>
        <Link to="/Index">
          <button>
            <p className={'font-aeonikBold text-[16px] leading-5 hover:text-[#006F33]'}>
              Index
            </p>
          </button>
        </Link>
      </div>
      <div></div>
    </div>
  );

  return <CommonContext.Provider value={commonElement}>{children}</CommonContext.Provider>;
};

export const useCommonElement = (): React.ReactNode | null => {
  return useContext(CommonContext);
};
