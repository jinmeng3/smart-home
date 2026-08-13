<template>
    <svg
        xmlns="http://www.w3.org/2000/svg"
        style="position: absolute; width: 0; height: 0; overflow: hidden"
        aria-hidden="true"
    >
        <symbol id="icon-search" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="6.5" />
            <path d="m16 16 4 4" />
        </symbol>
        <symbol id="icon-chevron-down" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="m7 9.5 5 5 5-5" />
        </symbol>
        <symbol id="icon-chevron-left" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="m14.5 6-6 6 6 6" />
        </symbol>
        <symbol id="icon-chevron-right" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="m9.5 6 6 6-6 6" />
        </symbol>
        <symbol id="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round">
            <path d="M6 6l12 12M18 6 6 18" />
        </symbol>
        <symbol id="icon-plus" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round">
            <path d="M12 5v14M5 12h14" />
        </symbol>
        <symbol id="icon-check-circle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="m8 12.5 2.6 2.6L16.5 9" />
        </symbol>
        <symbol id="icon-info" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 11v6" />
            <circle cx="12" cy="7.5" r="1" fill="currentColor" stroke="none" />
        </symbol>
        <symbol id="icon-warning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.3 4.3 2.8 17.2A1.9 1.9 0 0 0 4.4 20h15.2a1.9 1.9 0 0 0 1.6-2.8L13.7 4.3a2 2 0 0 0-3.4 0Z" />
            <path d="M12 9v4" />
            <circle cx="12" cy="16.5" r=".8" fill="currentColor" stroke="none" />
        </symbol>
        <symbol id="icon-chat" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 11.5a8 8 0 0 1-8.5 8 8.8 8.8 0 0 1-3.4-.8L4 20l1.3-3.6A8 8 0 1 1 20 11.5Z" />
            <circle cx="8.5" cy="11.5" r=".8" fill="currentColor" stroke="none" />
            <circle cx="12" cy="11.5" r=".8" fill="currentColor" stroke="none" />
            <circle cx="15.5" cy="11.5" r=".8" fill="currentColor" stroke="none" />
        </symbol>
        <symbol id="icon-home" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="m3 11 9-8 9 8" />
            <path d="M5 9.5V21h14V9.5" />
            <path d="M9 21v-6h6v6" />
        </symbol>
        <symbol id="icon-room" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17" />
            <path d="M3 21h18" />
            <circle cx="15.5" cy="12" r=".8" fill="currentColor" stroke="none" />
        </symbol>
        <symbol id="icon-device-management" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="12" height="16" rx="2" />
            <path d="M7 8h4" />
            <circle cx="9" cy="16" r="1.5" />
            <circle cx="18" cy="9" r="3" />
            <path d="M18 7.5V9l1 1" />
        </symbol>
        <symbol id="icon-scene" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 3 2.7 5.5 6 .9-4.3 4.2 1 6-5.4-2.9-5.4 2.9 1-6-4.3-4.2 6-.9L12 3Z" />
        </symbol>
        <symbol id="icon-automation" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="4" r="2" />
            <circle cx="5" cy="18" r="2" />
            <circle cx="19" cy="18" r="2" />
            <path d="M12 6v5M6.5 16.5 10.5 12M17.5 16.5 13.5 12" />
        </symbol>
        <symbol id="icon-energy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 20V12M8 20V7M12 20V10M16 20V4M20 20V14" />
            <path d="M3 20h18" />
        </symbol>
        <symbol id="icon-calendar" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 3v4M17 3v4M4 9h16" />
            <rect x="4" y="5" width="16" height="16" rx="2" />
            <path d="M8 13h3M8 17h6" />
        </symbol>
        <symbol id="icon-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8.5 15.5A6 6 0 1 1 15.5 15.5c-.9.7-1.2 1.3-1.3 2.1H9.8c-.1-.8-.4-1.4-1.3-2.1Z" />
            <path d="M9.5 20h5M10.5 17.5h3" />
        </symbol>
        <symbol id="icon-air-conditioner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v20M4.2 6.5l15.6 11M19.8 6.5l-15.6 11" />
            <path d="m9.5 4.5 2.5 2 2.5-2M9.5 19.5l2.5-2 2.5 2" />
            <path d="m5 9 3-.5-.3-3M19 15l-3 .5.3 3M19 9l-3-.5.3-3M5 15l3 .5-.3 3" />
        </symbol>
        <symbol id="icon-security" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3 20 6v5c0 5-3.4 8.2-8 10-4.6-1.8-8-5-8-10V6l8-3Z" />
            <path d="m8.5 12 2.2 2.2 4.8-5" />
        </symbol>
        <symbol id="icon-settings" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19 13.5a7 7 0 0 0 0-3l2-1.5-2-3.4-2.5 1a8 8 0 0 0-2.5-1.5L13.7 2h-4L9.3 5.1a8 8 0 0 0-2.5 1.5l-2.5-1-2 3.4 2 1.5a7 7 0 0 0 0 3l-2 1.5 2 3.4 2.5-1a8 8 0 0 0 2.5 1.5l.4 3.1h4l.4-3.1a8 8 0 0 0 2.5-1.5l2.5 1 2-3.4-2.1-1.5Z" />
        </symbol>
        <symbol id="icon-account" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />
            <path d="M4 21a8 8 0 0 1 16 0" />
        </symbol>
        <symbol id="icon-bell" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
            <path d="M10 21h4" />
        </symbol>
        <symbol id="icon-online-device" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <rect x="7" y="3" width="10" height="18" rx="2.5" />
            <path d="M10 6h4M11 18h2" />
            <path d="m9.5 12 1.7 1.7 3.5-4" />
        </symbol>
        <symbol id="icon-offline-device" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <rect x="7" y="3" width="10" height="18" rx="2.5" />
            <path d="M10 6h4M11 18h2" />
            <path d="m9.5 10 5 5M14.5 10l-5 5" />
        </symbol>
    </svg>
</template>
