/* Memory layout for nRF52833 with SoftDevice S140 v7.3.0 */
MEMORY
{
  /* SoftDevice S140 v7.3.0 uses 0x27000 bytes (156 KB) */
  /* Application starts after SoftDevice */
  FLASH : ORIGIN = 0x00027000, LENGTH = 356K
  
  /* RAM layout: SoftDevice uses the beginning of RAM */
  /* S140 v7.3.0 uses 0x3938 bytes minimum */
  RAM : ORIGIN = 0x20003938, LENGTH = 113864
}
