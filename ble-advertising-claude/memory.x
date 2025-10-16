/* Memory layout for nRF52840 with S140 SoftDevice v7.3.0 
 * 
 * SoftDevice S140 v7.3.0 Memory Usage:
 * - FLASH: 0x00000000 - 0x00027000 (156 KB)
 * - RAM:   0x20000000 - 0x20020000 (128 KB)
 * 
 * Application Memory (what's left):
 * - FLASH: 0x00027000 - 0x00100000 (868 KB available)
 * - RAM:   0x20020000 - 0x20040000 (128 KB available)
 */

MEMORY
{
  /* Application FLASH starts after SoftDevice (156 KB) */
  FLASH : ORIGIN = 0x00027000, LENGTH = 868K
  
  /* Application RAM starts after SoftDevice (128 KB reserved) */
  RAM : ORIGIN = 0x20020000, LENGTH = 128K
}

/* This is where the call stack will be allocated. */
/* The stack is of the full descending type. */
/* NOTE: You may want to increase this depending on your application needs */
_stack_start = ORIGIN(RAM) + LENGTH(RAM);
