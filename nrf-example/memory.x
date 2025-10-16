/* Linker script for the nRF52833 */
MEMORY
{
  /* SoftDevice S140 v7.3.0 takes 0x27000 bytes (156KB) */
  FLASH : ORIGIN = 0x00027000, LENGTH = 356K
  RAM : ORIGIN = 0x20003500, LENGTH = 114K
}

INCLUDE defmt.x
