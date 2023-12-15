import React from 'react'

interface CustomSVGProps {
  color: string
}

const CustomUpload: React.FC<CustomSVGProps> = ({ color }) => {
  return (
    <svg width="12" height="15" viewBox="0 0 12 15" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4.00008 6.33333V5.83333H3.50008H1.37385L6.00008 1.20711L10.6263 5.83333H8.50008H8.00008V6.33333V10.8333H4.00008V6.33333ZM11.3334 13.5V14.1667H0.666748V13.5H11.3334Z" fill={color} stroke={color} />
    </svg>
  )
}

export default CustomUpload
