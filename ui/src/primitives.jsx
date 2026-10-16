import React from 'react';
import {Icon} from './icons.jsx';
export function Button({children,icon,kind='',className='',...props}) {return <button className={`hl-btn ${kind} ${className}`} {...props}>{icon&&<Icon name={icon}/>}<span>{children}</span></button>;}
