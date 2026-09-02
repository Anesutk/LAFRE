export function Icon({name, size=18, strokeWidth=1.9}){
  const common={width:size,height:size,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor',strokeWidth,strokeLinecap:'round',strokeLinejoin:'round'};
  const paths={
    home:<><path d="m3 10 9-7 9 7"/><path d="M5 9v11h14V9"/><path d="M9 20v-6h6v6"/></>,
    forum:<><path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/></>,
    lawyer:<><circle cx="9" cy="8" r="3"/><path d="M3.5 20c.8-4 2.7-6 5.5-6s4.7 2 5.5 6"/><path d="M16 5h5M18.5 3v4M15 12a4 4 0 0 0 4 4h2"/></>,
    message:<><path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/></>,
    users:<><circle cx="8" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M2.5 20c.7-4 2.6-6 5.5-6s4.8 2 5.5 6M14 14c3.2-.1 5.2 2 5.6 5"/></>,
    brief:<><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M8 6V4h8v2M3 11h18M10 11v3h4v-3"/></>,
    tool:<><path d="m14 6 4 4M4 20l7-7M13 4a4 4 0 0 1 5.7 5.7l-8.1 8.1a3 3 0 0 1-4.2-4.2L14.5 5.5"/></>,
    search:<><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    bell:<><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>,
    user:<><circle cx="12" cy="8" r="3"/><path d="M5 21c.9-4.3 3.2-6 7-6s6.1 1.7 7 6"/></>,
    arrow:<><path d="M5 12h14M13 6l6 6-6 6"/></>,
    plus:<><path d="M12 5v14M5 12h14"/></>,
    close:<><path d="m6 6 12 12M18 6 6 18"/></>,
    chevron:<path d="m7 10 5 5 5-5"/>,
    like:<><path d="M7 10v10H4V10zM7 19h9a2 2 0 0 0 1.9-1.4l2-6A2 2 0 0 0 18 9h-4l.6-3.1A2 2 0 0 0 12.7 3L7 10"/></>,
    share:<><path d="m14 5 7 7-7 7"/><path d="M21 12H9a6 6 0 0 0-6 6"/></>,
    bookmark:<><path d="M6 4h12v17l-6-4-6 4z"/></>,
    flag:<><path d="M5 21V4"/><path d="M5 5h12l-2 4 2 4H5"/></>,
    sparkle:<><path d="m12 3 1.4 4.6L18 9l-4.6 1.4L12 15l-1.4-4.6L6 9l4.6-1.4z"/><path d="m19 15 .7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7z"/></>,
    logout:<><path d="M10 17l5-5-5-5M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-5"/></>,
    menu:<><path d="M4 6h16M4 12h16M4 18h16"/></>,
  };
  return <svg {...common}>{paths[name]}</svg>;
}
