/******************************************************************************************
*
*    Arise2 SOC Hardware resource config
*    (It is must sync with the bus.io and others that was supplied by HW designe)
*
*******************************************************************************************/

#ifndef  __ARISE2_SOC_HW_CONFIG
#define  __ARISE2_SOC_HW_CONFIG

/***********************************
* DRAM 64bit interlace dual channel
************************************/

#define RESERVED4_BASE             0x8000000000ULL
#define PCIE2_ECM_BASE             0x4000000000ULL
#define PCIE2_ECM_SIZE             (RESERVED4_BASE-PCIE2_ECM_BASE)
#define RESERVED3_BASE             0x1040000000ULL
#define PCIE1_ECM_BASE             0x1000000000ULL
#define PCIE1_ECM_SIZE             (RESERVED3_BASE-PCIE1_ECM_BASE)
#define DRAM1_BASE                 0x0880000000ULL
#define DRAM1_SIZE                 (PCIE1_ECM_BASE-DRAM1_BASE)
#define RESERVED2_BASE             0x0800000000ULL
#define RESERVED2_SIZE             (DRAM1_BASE-RESERVED2_BASE)
#define RESERVED1_BASE             0x0100000000
#define RESERVED1_SIZE             (RESERVED2_BASE-RESERVED1_BASE)
#define DRAM0_BASE                 0x0080000000
#define DRAM0_SIZE                 (RESERVED1_BASE-DRAM0_BASE)
#define CMN_HND_BASE               0x007C000000ULL
#define CMN_HND_SIZE               (DRAM0_BASE-CMN_HND_BASE)
#define PCIE0_MMIO_BASE            0x0078000000ULL
#define PCIE0_MMIO_SIZE            (CMN_HND_BASE-PCIE0_MMIO_BASE)
#define AP_PERI_BASE               0x0060000000ULL
#define AP_PERI_SIZE               (PCIE0_MMIO_BASE-AP_PERI_BASE)
#define SCP_PERI_BASE              0x0050000000ULL
#define SCP_PERI_SIZE              (AP_PERI_BASE-SCP_PERI_BASE)
#define PCIE0_BASE                 0x0020000000ULL
#define PCIE0_SIZE                 (SCP_PERI_BASE-PCIE0_BASE)
#define RESERVED0_BASE             0x0018000000ULL
#define RESERVED0_SIZE             (PCIE0_BASE-RESERVED0_BASE)
#define SMC_BASE                   0x0008000000ULL
#define SMC_SIZE                   (RESERVED0_BASE-SMC_BASE)
#define BOOT_BASE                  0x0000000000ULL
#define BOOT_SIZE                  (SMC_BASE-BOOT_BASE)

#define GIC_SPI_BASE               32
#define GIC_PPI_BASE               16

/* used by qemu */
#define PCIE_BASE0                 PCIE0_BASE
#define PCIE_SIZE0                 PCIE0_SIZE

/************************
* SOCAXI0 64bit@500MHz  
*************************/
#define SEC_ROM_BASE               0x00000000
#define SEC_ROM_SIZE               0x00020000

#define QEMU_VIRT_NUM              32
#define QEMU_VIRT_SIZE             0x00000200
#define QEMU_VIRT_BASE             (0x04000000 - (QEMU_VIRT_NUM*QEMU_VIRT_SIZE))


#define SEC_SRAM_SDS_BASE          0x04000000
#define SEC_SRAM_SDS_SIZE          0x00001000
#define AP_SEC_SRAM_BASE           0x04001000
#define AP_SEC_SRAM_SIZE           0x0005f000
#define SEC_SRAM_BASE              SEC_SRAM_SDS_BASE
#define SEC_SRAM_SIZE              (SEC_SRAM_SDS_SIZE+AP_SEC_SRAM_SIZE)

#define NSEC_SRAM_SHR_BASE         0x04060000
#define NSEC_SRAM_SHR_SIZE         0x00002000
#define NSEC_SRAM_BASE             0x04062000
#define NSEC_SRAM_SIZE             0x0001E000
#define TPM_PPI_BASE               NSEC_SRAM_BASE
#define TPM_PPI_SIZE               0x1000

#define AP_NSEC_SRAM_BASE          (NSEC_SRAM_SHR_BASE)
#define AP_NSEC_SRAM_SIZE          (NSEC_SRAM_SHR_SIZE+NSEC_SRAM_SIZE)

#define NSEC_ROM_BASE              0x04080000
//actual 64KB but debug version ns_bl1u may larger than 64KB
#define NSEC_ROM_SIZE              0x00020000

#define EMMC_BOOT_BASE             0x08000000
#define EMMC_BOOT_SIZE             0x00100000
#define EMMC_BOOT_PART_SIZE        0x00400000
//64Kb SRAM for cm4 use
/***********************************
 *
 *            EMMC_CM4_REVD
 *
 *      -----------------------------
 *      |                            |
 *      |  REV (no used)    (8KB)    |
 *      -----------------------------
 *      |                            |
 *      |  EMMC_CM4_TIME_TB (2KB)    |
 *      -----------------------------
 *      |                            |
 *      |  EMMC_CM4_DDR_CONG(6KB)    |
 *      -----------------------------
 *      |                            |
 *      |  EMMC_CM4_HEAP    (28KB)   |
 *      -----------------------------
 *      |                            |
 *      |  REV (no used)    (16KB)   |
 *      -----------------------------
 *      | CM4<->ADSP Communtion(4KB) |
 *      -----------------------------
 * ********************************/
#define EMMC_CM4_REVD_SIZE         0x00010000
#if defined(TARGET_MACHINE_ARISE_QEMU)
#define EMMC_CM4_REVD_BASE         (EMMC_BOOT_BASE + EMMC_BOOT_PART_SIZE)
#else
#define EMMC_CM4_REVD_BASE         (EMMC_BOOT_BASE + EMMC_BOOT_SIZE - EMMC_CM4_REVD_SIZE)
#endif

#define EMMC_CM4_TIME_TB_BASE      (EMMC_CM4_REVD_BASE + 0x00002000)
#define EMMC_CM4_TIME_TB_LENG      0x00000600
#define EMMC_CM4_TIME_TB_SIZE      0x00000800

#define EMMC_CM4_DDR_CONG_BASE     (EMMC_CM4_TIME_TB_BASE + EMMC_CM4_TIME_TB_SIZE)
#define EMMC_CM4_DDR_CONG_LENG     0x00000200
#define EMMC_CM4_DDR_CONG_SIZE     0x00001800

#define EMMC_CM4_HEAP_BASE         (EMMC_CM4_DDR_CONG_BASE + EMMC_CM4_DDR_CONG_SIZE)
#define EMMC_CM4_HEAP_SIZE         0x00007000

#define EMMC_CM4_ADSP_COMM_SIZE    0x00001000
#define EMMC_MB_CM4_ADSP_COMM_BASE (EMMC_BOOT_BASE + EMMC_BOOT_SIZE -(EMMC_CM4_ADSP_COMM_SIZE/2))
#define EMMC_MB_ADSP_CM4_COMM_BASE (EMMC_BOOT_BASE + EMMC_BOOT_SIZE - EMMC_CM4_ADSP_COMM_SIZE)

#define NORFLASH_BOOT_BASE         0x10000000
#define NORFLASH_BOOT_SIZE         0x00800000
#define NV_VARIABLE_SIZE           0x10000
#define NV_FTW_SPARE_SIZE          0x10000
#define NV_FTW_WORK_SIZE           0x10000

#define GICD_BASE                  0x70000000
#define GICD_SIZE                  0x00010000

#define GIC_ITS_BASE               0x70040000
#define GIC_ITS_SIZE               0x00020000

#define GIC_REDIST_BASE            0x70060000
#define GIC_REDIST_SIZE            0x00100000

#define UEFI_DEVICE_BASE           0x50000000
#define UEFI_DEVICE_SIZE           0x20300000

/***********************************
* System CMN600
************************************/
#define CMN600_ROOTNODE_OFFSET     0xC00000
#define CMN600_ROOTNODE_SIZE       0x4000


/************************
* SOCAXI1 32bit@500MHz  
*************************/
#define SOC_DMA3_BASE              0x65000000
#define SOC_DMA3_SIZE              0x00010000

#define SATA0_BASE                 0x65010000
#define SATA0_SIZE                 0x10000

#define SATA1_BASE                 0x65020000
#define SATA1_SIZE                 0x10000

#define PCIE_RC0_DBI_BASE          (0x66000000+0x800000)
#define PCIE_RC0_DBI_SIZE          0x300000

#define PCIE_RC0_ATU_BASE          (PCIE_RC0_DBI_BASE+PCIE_RC0_DBI_SIZE)
#define PCIE_RC0_ATU_SIZE          0x20000

#define PCIE_RC1_DBI_BASE          (0x67000000+0x800000)
#define PCIE_RC1_DBI_SIZE          0x300000

#define PCIE_RC1_ATU_BASE          (PCIE_RC1_DBI_BASE+PCIE_RC1_DBI_SIZE)
#define PCIE_RC1_ATU_SIZE          0x20000

/* USBH 250MHZ */
#define USB31_HOST0_BASE           0x68100000
#define USB31_HOST0_SIZE           0x00010000

#define USB31_HOST1_BASE           0x68110000
#define USB31_HOST1_SIZE           0x00010000

#define USB20_HOST0_BASE           0x68200000
#define USB20_HOST0_SIZE           0x00010000

#define USB20_HOST1_BASE           0x68300000
#define USB20_HOST1_SIZE           0x00010000

#define USB31_TCA0_BASE            0x68500000
#define USB31_TCA0_SIZE            0x00010000

#define USB31_TCA1_BASE            0x68510000
#define USB31_TCA1_SIZE            0x00010000

#define USB0_MISC_BASE             0x68520000
#define USB0_MISC_SIZE             0x00010000

#define USB1_MISC_BASE             0x68530000
#define USB1_MISC_SIZE             0x00010000

#define USB2_MISC_BASE             0x68540000
#define USB2_MISC_SIZE             0x00040000

#define USB3_MISC_BASE             0x68580000
#define USB3_MISC_SIZE             0x00040000

/* SDH 250MHZ */
#define SD_HOST_BASE               0x60B00000
#define SD_HOST_SIZE               0x00010000

#define SDIO_HOST_BASE             0x60B10000
#define SDIO_HOST_SIZE             0x00010000

#define EMMC_HOST_BASE             0x60B20000
#define EMMC_HOST_SIZE             0x00010000


/* ETH controller */
#define GMAC0_BASE                 0x60b30000
#define GMAC0_SIZE                 0x00010000

#define GMAC1_BASE                 0x60b40000
#define GMAC1_SIZE                 0x00010000

#define GMAC2_BASE                 0x60b50000
#define GMAC2_SIZE                 0x00010000



/* 32bit@250MHz*/
#define SOC_PMU_BASE               0x60300000
#define SOC_PMU_SIZE               0x00010000
#define SOC_PMU_WAKE_STA           0xFC              /* inside 0f 0x100 */

#define SOC_PMU_RESET_BASE         0x60310000
#define SOC_PMU_RESET_SIZE         0x00010000

/* AMU */
#define CORE0_AMU_BASE             0x618F0000
#define CORE1_AMU_BASE             0x619F0000
#define CORE2_AMU_BASE             0x61AF0000
#define CORE3_AMU_BASE             0x61BF0000
#define CORE4_AMU_BASE             0x61CF0000
#define CORE5_AMU_BASE             0x61DF0000
#define CORE6_AMU_BASE             0x61EF0000
#define CORE7_AMU_BASE             0x61FF0000

#define AMU_SIZE                   0X800000

#define AMEVCNTR0_OFFSET           0x0
#define AMEVCNTR1_OFFSET           0x8
#define AMEVCNTR2_OFFSET           0x10
#define AMEVCNTR3_OFFSET           0x18
#define AMEVCNTR10_OFFSET          0x100
#define AMEVCNTR11_OFFSET          0x108
#define AMEVCNTR12_OFFSET          0x110

/* Mailbox */
#define MB_BASE                    0x50380000
#define MB_SIZE                    0x000000E8
#define MB_INDIRECT_INT_GEN        0x00
#define MB_INDIRECT_INT_CLR        0x04
#define MB_INDIRECT_INT_STA        0x08
#define MB_SCP_AP_INT_GEN          0x0c
#define MB_SCP_AP_CLR              0x10
#define MB_SCP_AP_STAT             0x14
#define MB_AP_SCP_INT_GEN          0x30
#define MB_AP_SCP_CLR              0x34
#define MB_AP_SCP_STAT             0x38
#define MB_ADSP_SCP_INT_GEN        0x3C
#define MB_ADSP_SCP_CLR            0x40
#define MB_ADSP_SCP_STAT           0x44
#define MB_SCP_ADSP_INT_GEN        0x60
#define MB_SCP_ADSP_CLR            0x64
#define MB_SCP_ADSP_STAT           0x68
#define MB_SEC_SCP_AP_INT_GEN      0x9c
#define MB_SEC_SCP_AP_CLR          0xa0
#define MB_SEC_SCP_AP_STAT         0xa4
#define MB_SEC_AP_SCP_INT_GEN      0xa8
#define MB_SEC_AP_SCP_CLR          0xac
#define MB_SEC_AP_SCP_STAT         0xb0
#define MB_SEC_INT_MASK            0xb4
#define MB_CM4_A78_S_ADDR          0xb8
#define MB_A78_CM4_S_ADDR          0xC4
#define MB_ADSP_CM4_S_ADDR         0xC8
#define MB_CM4_ADSP_S_ADDR         0xD4


#define MB_SEC_BASE                MB_BASE

/*NOC_MMIO_REG_BASE used in GPU ROM*/
#define  NOC_MMIO_REG_BASE         0x58100000

/* GPU Mailbox lite*/
#define MB_LITE_BASE               0x583e0000
#define MB_LITE_WBUFF_SIZE         0x200
#define MB_LITE_IRQ_GEN            0x200
#define MB_LITE_IRQ_STATUS         0x204
#define MB_LITE_MESSAGE_CNT        0x208

/* CPU Freq CPPC PCC Shared Memory */
#define PCC_SHR_BASE                (NSEC_SRAM_SHR_BASE + 0x180)
#define PCC_SHR_SIZE                0x200

/* Thermal Zone 2 temperature Shared Memory*/
#define TZ2_SHR_BASE                (PCC_SHR_BASE+PCC_SHR_SIZE)
#define TZ2_SHR_SIZE                0x4

#define GTIMER_CTL_SHR_BASE         ((TZ2_SHR_BASE + TZ2_SHR_SIZE + 0xff) & ~0xff)
#define GTIMER_CTL_SHR_SIZE         0x100

#define GTIMER_FRAME_SHR_BASE       (GTIMER_CTL_SHR_BASE + GTIMER_CTL_SHR_SIZE)
#define GTIMER_FRAME_SHR_SIZE       0x100

/* SF REG */
#define BOOT_SPI_REG_BASE          0x60200000
#define BOOT_SPI_REG_SIZE          0x10000
#define SUS_MISC_SPI               0x60440000

#define SATA_PHY_CFG_BASE          0x60440068
#define E32_PHY1_REG_BASE          0x52000000
#define E32_PHY2_REG_BASE          0x52100000

#define BOOT_CSPI_REG_BASE          0x18000000
#define BOOT_CSPI_REG_SIZE          0x10000
#define BOOT_CSPI_MMAP_BASE         0x10000000
#define SUS_MISC_CSPI               0x50390000

#define SOC_COPLL_CTRL_BASE        0x60420000
#define SOC_COPLL_CTRL_SIZE        0x00010000

#define SOC_C1PLL_CTRL_BASE        0x60430000
#define SOC_C1PLL_CTRL_SIZE        0x00010000

#define SOC_CCP_SOC_C_BASE         0x60400000
#define SOC_CCP_SOC_C_SIZE         0x00010000

#define SOC_CCP_SOC_S_BASE         0x60410000
#define SOC_CCP_SOC_S_SIZE         0x00010000

/************************
* SOCAPB0 32bit@125MHz  
*************************/
#define UART2_BASE                 0x60780000
#define UART2_SIZE                 0x00010000

#define UART3_BASE                 0x60790000
#define UART3_SIZE                 0x00010000

#define SOC_GPIO_BASE              0x607C0000
#define SOC_GPIO_SIZE		   0x00010000
#define SOC_ARM_GPIO_SIZE          0x00001000

#define WDT0_BASE                  0x607a0000
#define WDT0_SIZE                  0x10000

#define WDT1_BASE                  0x607b0000
#define WDT1_SIZE                  0x10000

/************************
* SOCAPB1 32bit@125MHz  
*************************/
#define SOC_PCM6_BASE              0x60D00000
#define SOC_PCM6_SIZE              0x00010000

#define SOC_PCM7_BASE              0x60D10000
#define SOC_PCM7_SIZE              0x00010000

#define SOC_SPDIF1_BASE            0x60D20000
#define SOC_SPDIF1_SIZE            0x00010000

#define SOC_TIME0_BASE             0x60d30000
#define SOC_TIME0_SIZE             0x00010000

#define SOC_TIME1_BASE             0x60d40000
#define SOC_TIME1_SIZE             0x00010000

// for VDK test
#define SOC_PL111_BASE             0x60d70000
#define SOC_PL111_SIZE             0x00010000

#define SOC_I2C6_BASE              0x60700000
#define SOC_I2C6_SIZE              0x10000

#define SOC_I2C7_BASE              0x60710000
#define SOC_I2C7_SIZE              0x10000

#define SOC_I2C8_BASE              0x60720000
#define SOC_I2C8_SIZE              0x10000

#define SOC_I2C9_BASE              0x60730000
#define SOC_I2C9_SIZE              0x10000

#define SOC_I2C10_BASE             0x60740000
#define SOC_I2C10_SIZE             0x10000

#define SOC_I2C11_BASE             0x60750000
#define SOC_I2C11_SIZE             0x10000

#define SOC_SPI3_BASE              0x60760000
#define SOC_SPI3_SIZE              0x10000

#define SOC_SPI4_BASE              0x60770000
#define SOC_SPI4_SIZE              0x10000

#define SOC_DAP_BASE               0x61000000
#define SOC_DAP_SIZE               0x1000000

/************************
* MMUAPB 32bit@125MHz  
*************************/
#define BMMMU_BASE                 0x62800000
#define BMMMU_SIZE                 0x00800000
#define RCMMU_BASE                 0x63000000
#define RCMMU_SIZE                 0x00800000
#define VENGMMU_BASE               0x63800000
#define VENGMMU_SIZE               0x00800000




/************************
* SCPAHB 32bit@250MHz  
*************************/

#define SCP_SEC_ROM_BASE           0x00000000
#define SCP_SEC_ROM_SIZE           0x00010000

#define SCP_SEC_SRAM_BASE          0x04200000
#define SCP_SEC_SRAM_SIZE          0x00020000

#define SCP_NIC400_BASE            0x4100000

/************************
* SUSAHB0 32bit@250MHz  
*************************/
#define EFUSE_SRAM0_BASE           0x5040FC00
#define EFUSE_SRAM0_SIZE           0x00000200
#define EFUSE_SRAM1_BASE           0x5040FE00
#define EFUSE_SRAM1_SIZE           0x00000200
#define EFUSE_SRAM_BASE            EFUSE_SRAM0_BASE
#define EFUSE_SRAM_SIZE            (EFUSE_SRAM0_SIZE+EFUSE_SRAM1_SIZE)

#define EFUSE_CTRL_BASE            0x50400000

#define PCIE_DM_DBI_BASE           (0x55000000+0x800000)
#define PCIE_DM_DBI_SIZE           0x300000
#define PCIE_DM_ATU_BASE           (PCIE_DM_DBI_BASE+PCIE_DM_DBI_SIZE)
#define PCIE_DM_ATU_SIZE           0x20000

#define SUS_PMU_BASE               0x50100000
#define SUS_PMU_SIZE               0x00200000

#define SUS_PMU_RESET_BASE         0x50110000
#define SUS_PMU_RESET_SIZE         0x00010000

#define SUS_DMA0_BASE              0x50e00000
#define SUS_DMA0_SIZE              0x00010000

#define SUS_DMA1_BASE              0x583d0000
#define SUS_DMA1_SIZE              0x00010000

#define SUS_DMA2_BASE              0x50e20000
#define SUS_DMA2_SIZE              0x00010000

#define SUS_DMA0_MUX 		   0x5043005c
#define SUS_DMA1_MUX 		   0x50430054
#define SUS_DMA2_MUX 		   0x50430050

#define CM4_TIMER_BASE             0x50200000
#define CM4_TIMER_SIZE             0x00010000

#define CM4_WDT_BASE               0x50210000
#define CM4_WDT_SIZE               0x00010000

#define SUSMMU_BASE                0x52200000
#define SUSMMU_SIZE                0x00800000

/************************
* SUSAPB0 32bit@125MHz  
*************************/
#define UART0_BASE                 0x50990000
#define UART0_SIZE                 0x00010000

#define UART1_BASE                 0x509A0000
#define UART1_SIZE                 0x00010000

#define SUS_GPIO_BASE              0x583A0000
#define SUS_GPIO_SIZE              0x00010000
#define	SUS_ARM_GPIO_SIZE          0x00001000

#define SUS_MISC_BASE              0x583A1000
#define SUS_MISC_SIZE              0x0001000

#define SUS_PWM_BASE               0x509C0000
#define SUS_PWM_SIZE               0x00010000

#define SUS_I2C0_BASE              0x50900000
#define SUS_I2C0_SIZE              0x00010000

#define SUS_I2C1_BASE              0x50910000
#define SUS_I2C1_SIZE              0x00010000

#define SUS_I2C2_BASE              0x50920000
#define SUS_I2C2_SIZE              0x00010000

#define SUS_I2C3_BASE              0x50930000
#define SUS_I2C3_SIZE              0x00010000

#define SUS_I2C4_BASE              0x50940000
#define SUS_I2C4_SIZE              0x00010000

#define SUS_I2C5_BASE              0x50950000
#define SUS_I2C5_SIZE              0x00010000

#define SUS_SPI0_BASE              0x50960000
#define SUS_SPI0_SIZE              0x00010000

#define SUS_SPI1_BASE              0x50970000
#define SUS_SPI1_SIZE              0x00010000

#define SUS_SPI2_BASE              0x50980000
#define SUS_SPI2_SIZE              0x00010000

#define SUS_TS_BASE                0x50300000
#define SUS_TS_SIZE                0x00010000

#define SUS_FAN0_BASE              0x50310000
#define SUS_FAN0_SIZE              0x00010000

#define SUS_FAN1_BASE              0x50320000
#define SUS_FAN1_SIZE              0x00010000

#define SUS_WAKE_VIC_BASE          0x503b0000
#define SUS_WAKE_VIC_SIZE          0x00010000

#define SUS_APLL_CTRL_BASE         0x50360000
#define SUS_APLL_CTRL_SIZE         0x00010000

#define SUS_SPLL_CTRL_BASE         0x50350000
#define SUS_SPLL_CTRL_SIZE         0x00010000

#define SUS_CCP_SUS_A_BASE         0x50330000
#define SUS_CCP_SUS_A_SIZE         0x00010000

#define SUS_CCP_SUS_S_BASE         0x50340000
#define SUS_CCP_SUS_S_SIZE         0x00010000

#define SUS_ADC_BASE               0x50370000
#define SUS_ADC_SIZE               0x00010000

#define SUS_SYS_BASE               0x50390000
#define SUS_SYS_SIZE               0x00010000
#define SUS_SYS_AUDIO_CLK_EN       0x00000198
#define SUS_SYS_AUDIO_CLK_SEL      0x0000019C
/************************
* MEMAPB 32bit@125MHz  
*************************/
#define TZC400_BASE0               0x51100000
#define TZC400_SIZE0               0x00010000

#define TZC400_BASE1               0x51110000
#define TZC400_SIZE1               0x00010000

#define DRMA_CTRL0_BASE            0x51120000
#define DRMA_CTRL0_SIZE            0x00010000

#define DRMA_CTRL1_BASE            0x51140000
#define DRMA_CTRL1_SIZE            0x00010000

#define SYS_CNT_BASE               0x50B20000
#define SYS_CNT_READ_BASE          0x50B30000

#define VMEM_HASH_BASE             0x511A0000
#define VMEM_HASH_SIZE             0x00010000

#define VMEM_MISC_BASE             0x511B0000
#define VMEM_MISC_SIZE             0x00010000

#define VMEM_MISC_SE_BASE          0x511C0000
#define VMEM_MISC_SE_SIZE          0x00010000

#define VMM_HASH_BASE              0x582E0000
#define VMM_HASH_SIZE              0x00010000

/************************
* SUSAPB2 32bit@125MHz  
*************************/
#define SEC_ENG_BASE               0x583F0000
#define SEC_ENG_SIZE               0x00010000

#define SUS_TIME0_BASE             0x50DA0000
#define SUS_TIME0_SIZE             0x00010000

#define SUS_TIME1_BASE             0x50DB0000
#define SUS_TIME1_SIZE             0x00010000

#define SUS_PCM0_BASE              0x50D00000
#define SUS_PCM0_SIZE              0x00010000

#define SUS_PCM1_BASE              0x50D10000
#define SUS_PCM1_SIZE              0x00010000

#define SUS_PCM2_BASE              0x50D20000
#define SUS_PCM2_SIZE              0x00010000

#define SUS_PCM3_BASE              0x50D30000
#define SUS_PCM3_SIZE              0x00010000

#define SUS_PCM4_BASE              0x50D40000
#define SUS_PCM4_SIZE              0x00010000

#define SUS_PCM5_BASE              0x583b0000
#define SUS_PCM5_SIZE              0x00010000

#define SUS_SPDIF0_BASE            0x583c0000
#define SUS_SPDIF0_SIZE            0x00010000

#define SUS_PDM_BASE               0x50D60000
#define SUS_PDM_SIZE               0x00010000

/************************
*  SUSAHB2 32bit@250MHz  
************************/
#define SUS_RTC_BASE               0x50B40000
#define SUS_RTC_SIZE               0x00010000

#define SUS_VBAT_RTC_BASE          0x50B50000
#define SUS_VBAT_RTC_SIZE          0x00010000


/************************
*  RCSAXI
************************/
#define PCIE_DM_ECAM_BASE          0x1000000000ULL
#define PCIE_DM_ECAM_SIZE          0x10000000
#define PCIE_DM_IO_SIZE            (16*1024*1024)
#define PCIE_DM_MEM0_BASE          0x20000000
#define PCIE_DM_MEM0_SIZE          (0x10000000 - PCIE_DM_IO_SIZE)
#define PCIE_DM_MEM1_BASE          0x4000000000ULL
#define PCIE_DM_MEM1_SIZE          0x2000000000ULL
#define PCIE_DM_IO_BASE            (PCIE_DM_MEM0_BASE+PCIE_DM_MEM0_SIZE)


#define PCIE_RC0_ECAM_BASE         0x1010000000ULL
#define PCIE_RC0_ECAM_SIZE         0x10000000
#define PCIE_RC0_IO_SIZE           (16*1024*1024)
#define PCIE_RC0_MEM0_BASE         0x30000000
#define PCIE_RC0_MEM0_SIZE         (0x10000000 - PCIE_RC0_IO_SIZE)
#define PCIE_RC0_MEM1_BASE         0x6000000000ULL
#define PCIE_RC0_MEM1_SIZE         0x1000000000ULL
#define PCIE_RC0_IO_BASE           (PCIE_RC0_MEM0_BASE+PCIE_RC0_MEM0_SIZE)

#define PCIE_RC1_ECAM_BASE         0x1020000000ULL
#define PCIE_RC1_ECAM_SIZE         0x10000000
#define PCIE_RC1_MEM0_BASE         0x40000000
#define PCIE_RC1_MEM0_SIZE         0x10000000
#define PCIE_RC1_MEM1_BASE         0x7000000000ULL
#define PCIE_RC1_IO_SIZE           (16*1024*1024)
#define PCIE_RC1_MEM1_SIZE         (0x1000000000ULL-PCIE_RC1_IO_SIZE)
#define PCIE_RC1_IO_BASE           (PCIE_RC1_MEM1_BASE+PCIE_RC1_MEM1_SIZE)

/************************
* MMSAXI 32bit@375MHz
************************/
#define VMM_EPLL_CTRL_BASE         0x50311000
#define VMM_EPLL_CTRL_SIZE         0x00001000

#define VMM_VPLL_CTRL_BASE         0x50312000
#define VMM_VPLL_CTRL_SIZE         0x00001000

#define VMM_CCP_VMM_V_BASE         0x50313000
#define VMM_CCP_VMM_V_SIZE         0x00001000

#define VMM_CCP_VMM_H_BASE         0x50314000
#define VMM_CCP_VMM_H_SIZE         0x00001000

#define VMM_SEC_MISC_BASE          0x58320000
#define VMM_SEC_MISC_SIZE          0x00010000


/***********************************
 *
 *   irq map
 *
 * *********************************/
/* GIC PPI */
#define GIC_PPI_PMU                7
#define GIC_PPI_MAINT              9
#define GIC_PPI_HYPTIMER           10
#define GIC_PPI_VIRTTIMER          11
#define GIC_PPI_HYVTIMER           12
#define GIC_PPI_SECTIMER           13
#define GIC_PPI_PHYSTIMER          14

/* SPI (base=0) */
// VSUS
#define IRQ_SUS_DMA0_CH0           5
#define IRQ_SUS_DMA0_CH1           6
#define IRQ_SUS_DMA0_CH2           7
#define IRQ_SUS_DMA0_CH3           8
#define IRQ_SUS_DMA0_CH4           9
#define IRQ_SUS_DMA0_CH5           10
#define IRQ_SUS_DMA0_CH6           11
#define IRQ_SUS_DMA0_CH7           12
#define IRQ_SUS_DMA1_CH0           13
#define IRQ_SUS_DMA1_CH1           14
#define IRQ_SUS_DMA1_CH2           15
#define IRQ_SUS_DMA1_CH3           16
#define IRQ_SUS_DMA1_CH4           17
#define IRQ_SUS_DMA1_CH5           18
#define IRQ_SUS_DMA1_CH6           19
#define IRQ_SUS_DMA1_CH7           20
#define IRQ_SUS_DMA2               21
#define IRQ_TE600_HOST0            22
#define IRQ_TE600_HOST1            23
#define IRQ_TE600_HOST2            24
#define IRQ_TE600_HOST3            25

#define IRQ_PCIE_DM_A              26
#define IRQ_PCIE_DM_B              27
#define IRQ_PCIE_DM_C              28
#define IRQ_PCIE_DM_D              29
#define IRQ_PCIE_DM_MSI            30

#define IRQ_UART0                  31    /* AP and SCP NVIC UART0 */
#define IRQ_UART1                  32    /* AP and SCP NVIC UART1 */

#define IRQ_SUS_GPIO_BANK0         33
#define IRQ_SUS_GPIO_BANK1         34
#define IRQ_SUS_GPIO_BANK2         35
#define IRQ_SUS_GPIO_BANK3         36

#define SUS_GPIO_RTC_WAKE_PIN      24

#define SOC_GPIO_LID_PIN           25
#define SOC_GPIO_EC_INTR_PIN       23
#define SOC_GPIO_EC_TEST_PIN       22
#define SOC_GPIO_KBC_PIN           21
#define SOC_GPIO_TPD_PIN           20
#define SOC_GPIO_MOUSE_PIN         19

#define IRQ_SUS_PWM                37
#define IRQ_TZC0                   45
#define IRQ_TZC1                   46
#define IRQ_RTC                    47

#define IRQ_I2S0                   48
#define IRQ_I2S1                   49
#define IRQ_I2S2                   50
#define IRQ_I2S3                   51
#define IRQ_I2S4                   52
#define IRQ_I2S5                   53

#define IRQ_PCM0                   48
#define IRQ_PCM1                   49
#define IRQ_PCM2                   50
#define IRQ_PCM3                   51
#define IRQ_PCM4                   52
#define IRQ_PCM5                   53

#define IRQ_SPDIF0                 60
#define IRQ_SUS_TIMER0             61
#define IRQ_SUS_TIMER1             62
#define IRQ_SUS_PMU                63
#define IRQ_ADC                    64
#define IRQ_TS                     65
#define IRQ_TS_HIGH                69

#define IRQ_OTP                    73

#define IRQ_I2C0                   74
#define IRQ_I2C1                   75
#define IRQ_I2C2                   76
#define IRQ_I2C3                   77
#define IRQ_I2C4                   78
#define IRQ_I2C5                   79

#define IRQ_SPI0                   80
#define IRQ_SPI1                   81
#define IRQ_SPI2                   82

#define IRQ_SUS_SF0                83
#define IRQ_CM4_WDT                84
#define IRQ_CM4_TIMER              85

#define IRQ_MB_A78                 88
#define IRQ_MB_CM4_A78_S           89
#define IRQ_MB_CM4_A78_NS          90
#define IRQ_MB_ADSP_A78            91
// #define IRQ_MB_VDSP_A78
#define IRQ_MB_CM4                 88
#define IRQ_MB_A78_CM4_S           89
#define IRQ_MB_A78_CM4_NS          90
#define IRQ_MB_ADSP_CM4            91
// #define IRQ_MB_VDSP_CM4
#define IRQ_VBAT_RTC               92
#define IRQ_MB_LITE_AP             93
#define IRQ_MB_LITE_SCP            93

#define IRQ_FAN0_AP                94
#define IRQ_FAN0_SCP               94
#define IRQ_FAN1_AP                95
#define IRQ_FAN1_SCP               95

#define IRQ_EMMC                   96
#define IRQ_EMMC_WAKEUP            97

#define IRQ_SD                     98
#define IRQ_SD_WAKEUP              99

#define IRQ_SDIO                   100
#define IRQ_SDIO_WAKEUP            101

#define IRQ_USB31_HOST0            102
#define IRQ_USB31_HOST1            103
#define IRQ_USB20_HOST0            104
#define IRQ_USB20_HOST1            105

#define IRQ_GMAC0                  107    // 107 ~ 111
#define IRQ_GMAC1                  112    // 112 ~ 116
#define IRQ_GMAC2                  117    // 117 ~ 120

#define IRQ_USB31_HOST0_TCA        121
#define IRQ_USB31_HOST1_TCA        122

//DRAMC
#define IRQ_DRAMC0_CH0_OVERTEMP    123
#define IRQ_DRAMC0_CH0_HIGHTEMP    124
#define IRQ_DRAMC0_CH0_COOLDOWN    125
#define IRQ_DRAMC0_CH0_PHY_ERR     126
#define IRQ_DRAMC0_CH0_ECC_SEC     127
#define IRQ_DRAMC0_CH0_ECC_DED     128
#define IRQ_DRAMC0_CH0_ECC_SEC_TH  129

#define IRQ_DRAMC0_CH1_OVERTEMP    130
#define IRQ_DRAMC0_CH1_HIGHTEMP    131
#define IRQ_DRAMC0_CH1_COOLDOWN    132
#define IRQ_DRAMC0_CH1_PHY_ERR     133
#define IRQ_DRAMC0_CH1_ECC_SEC     134
#define IRQ_DRAMC0_CH1_ECC_DED     135
#define IRQ_DRAMC0_CH1_ECC_SEC_TH  136

#define IRQ_DRAMC1_CH0_OVERTEMP    137
#define IRQ_DRAMC1_CH0_HIGHTEMP    138
#define IRQ_DRAMC1_CH0_COOLDOWN    139
#define IRQ_DRAMC1_CH0_PHY_ERR     140
#define IRQ_DRAMC1_CH0_ECC_SEC     141
#define IRQ_DRAMC1_CH0_ECC_DED     142
#define IRQ_DRAMC1_CH0_ECC_SEC_TH  143

#define IRQ_DRAMC1_CH1_OVERTEMP    144
#define IRQ_DRAMC1_CH1_HIGHTEMP    145
#define IRQ_DRAMC1_CH1_COOLDOWN    146
#define IRQ_DRAMC1_CH1_PHY_ERR     147
#define IRQ_DRAMC1_CH1_ECC_SEC     148
#define IRQ_DRAMC1_CH1_ECC_DED     149
#define IRQ_DRAMC1_CH1_ECC_SEC_TH  150

// VSOC
#define IRQ_SOC_TIMER0             151
#define IRQ_SOC_TIMER1             152

#define IRQ_WDT0                   153
#define IRQ_WDT1                   154

#define IRQ_SOC_PMU                155
#define IRQ_SATA0                  156
#define IRQ_SATA1                  157

#define IRQ_I2C6                   158
#define IRQ_I2C7                   159
#define IRQ_I2C8                   160
#define IRQ_I2C9                   161
#define IRQ_I2C10                  162
#define IRQ_I2C11                  163

#define IRQ_SPI3                   164
#define IRQ_SPI4                   165
#define IRQ_SOC_SF1                166

#define IRQ_UART2                  167    /* AP UART2 */
#define IRQ_UART3                  168    /* AP UART3 */

#define IRQ_SOC_DMA3               169
#define IRQ_SOC_GPIO_BANK0         170

#define IRQ_I2S6                   172
#define IRQ_I2S7                   173

#define IRQ_PCM6                   172
#define IRQ_PCM7                   173
#define IRQ_SPDIF1                 176

#define IRQ_GIC_FAULT              177
#define IRQ_GIC_ERR                178
#define IRQ_GIC_PMU                179

#define IRQ_PCIE_RC0_A             180
#define IRQ_PCIE_RC0_B             181
#define IRQ_PCIE_RC0_C             182
#define IRQ_PCIE_RC0_D             183
#define IRQ_PCIE_RC0_MSI           184

#define IRQ_PCIE_RC1_A             185
#define IRQ_PCIE_RC1_B             186
#define IRQ_PCIE_RC1_C             187
#define IRQ_PCIE_RC1_D             188
#define IRQ_PCIE_RC1_MSI           189

#define IRQ_CMN_PPU                190
#define IRQ_CMN_PMU                191
#define IRQ_CMN_ERR_NS             192
#define IRQ_CMN_ERR_S              193
#define IRQ_CMN_FAULT_NS           194
#define IRQ_CMN_FAULT_S            195

#define IRQ_RCMMU                  196    // 196 ~ 206
#define IRQ_VENGMMU                207    // 207 ~ 217
#define IRQ_SUSMMU                 218    // 218 ~ 228
#define IRQ_BMMMU                  229    // 229 ~ 239

#define IRQ_CSIH_0                 264
#define IRQ_CSIH_1                 265
#define IRQ_CSIL_0                 266
#define IRQ_CSIL_1                 267
#define IRQ_CSIL_2                 268
#define IRQ_CSIL_3                 269
#define IRQ_SIF                    270
#define IRQ_ISP_INTER_INT          278
#define IRQ_VMM_CTRL_INT           279

#define IRQ_WAKE_INTC              200
#define IRQ_VENG                   0

// SMMU IRQ OFFSET
#define OFFSET_EVENT_Q_S           0
#define OFFSET_EVENT_Q_NS          1
#define OFFSET_CMD_SYNC_S          2
#define OFFSET_CMD_SYNC_NS         3
#define OFFSET_GLOBAL_S            4
#define OFFSET_GLOBAL_NS           5
#define OFFSET_RCS_TCU             6
#define OFFSET_PMU_TCU             7
#define OFFSET_PRI_Q_NS            8
#define OFFSET_RCS_TBU             9
#define OFFSET_PMU_TBU             10


/***********************************
 *
 *        Assgin HandShake Signal
 *         Start	 End
 *  DMA0 : 0		 15
 *  DMA1 : 16        31
 *  DMA3 : 32        47
 *
 * *********************************/
//DMA3 Handshake Signal
#define DMA3_HS_UART3_TX           32
#define DMA3_HS_UART3_RX           33

#define DMA3_HS_UART2_TX           34
#define DMA3_HS_UART2_RX           35

#define DMA3_HS_SPI4_TX            36
#define DMA3_HS_SPI4_RX            37

#define DMA3_HS_SPI3_TX            38
#define DMA3_HS_SPI3_RX            39

#define DMA3_HS_I2S7_TX            40
#define DMA3_HS_I2S7_RX            41

#define DMA3_HS_I2S6_TX            42
#define DMA3_HS_I2S6_RX            43

#define DMA3_HS_SPDIF1_TX          44
#define DMA3_HS_SPDIF1_RX          45

//DMA0-MUX Handshake Signal
#define DMA_MUX_I2S0                0
#define HS_I2S0_TX                  0
#define HS_I2S0_RX                  1

#define DMA_MUX_I2S1                0
#define HS_I2S1_TX                  2
#define HS_I2S1_RX                  3

#define DMA_MUX_I2S2                0
#define HS_I2S2_TX                  4
#define HS_I2S2_RX                  5

#define DMA_MUX_I2S3                0
#define HS_I2S3_TX                  6
#define HS_I2S3_RX                  7

#define DMA_MUX_PDM0                0
#define HS_PDM0_TX                  -1
#define HS_PDM0_RX                  9

#define DMA_MUX_I2S4                0
#define HS_I2S4_TX                  12
#define HS_I2S4_RX                  13

//DMA1-MUX Handshake Signal
#define DMA_MUX_UART0               1
#define HS_UART0_TX                 16
#define HS_UART0_RX                 17

#define DMA_MUX_UART1               1
#define HS_UART1_TX                 18
#define HS_UART1_RX                 19

#define DMA_MUX_SPI0                1
#define HS_SPI0_TX                  20
#define HS_SPI0_RX                  21

#define DMA_MUX_SPI1                1
#define HS_SPI1_TX                  22
#define HS_SPI1_RX                  23

#define DMA_MUX_PDM1                1
#define HS_PDM1_TX                  -1
#define HS_PDM1_RX                  25

#define DMA_MUX_SPI2                1
#define HS_SPI2_TX                  26
#define HS_SPI2_RX                  27

#define DMA_MUX_SPDIF0              1
#define HS_SPDIF0_TX                28
#define HS_SPDIF0_RX                29

#define DMA_MUX_I2S5                1
#define HS_I2S5_TX                  30
#define HS_I2S5_RX                  31

//DMA2-MUX Handshake Signal

/***********************************
 *
 *   BMMMU SID
 *
 * *********************************/
#define BMMMU_SID_USB31_HOST0      0
#define BMMMU_SID_USB31_HOST1      1
#define BMMMU_SID_USB20_HOST0      2
#define BMMMU_SID_USB20_HOST1      3
#define BMMMU_SID_USB20_HOST2      4
#define BMMMU_SID_SATA0            5
#define BMMMU_SID_SATA1            6
#define BMMMU_SID_GMAC0            16
#define BMMMU_SID_GMAC1            24
#define BMMMU_SID_GMAC2            32
#define BMMMU_SID_EMMC             15
#define BMMMU_SID_SD               8
#define BMMMU_SID_SDIO             9
#define BMMMU_SID_DMAC3            7


/***********************************
 *
 *   RCMMU SID
 *
 * *********************************/
#define RCMMU_SID_RC0              0x00000
#define RCMMU_SID_RC1              0x10000
#define RCMMU_SID_DM               0x20000

/***********************************
 *
 *   SUSMMU SID
 *
 * *********************************/
#define SUSMMU_SID_DMA1            0x0
#define SUSMMU_SID_DMA2            0x0

#define SUSMMU_SID_TE_HOST0        0x6
#define SUSMMU_SID_TE_HOST1        0x7
#define SUSMMU_SID_TE_HOST2        0x8
#define SUSMMU_SID_TE_HOST3        0x9

/***********************************
 *
 * Memory Reserved region 0 Layout
 *
 *      -----0xFFFF_FFFF----
 *      |                  |
 *      |  SCP TZC (2MB)   |
 *      --------------------
 *      |                  |
 *      |  EL3 TZC (2MB)   |
 *      --------------------
 *      |                  |
 *      |  AP TZC (28MB)   |
 *      --------------------
 *      |                  |
 *      | OPTEE SHMEM(4MB) |
 *      --------------------
 *      |                  |
 *      |HW CFG(dtb)(256KB)|
 *      --------------------
 *      |                  |
 *      |ACPI_CHANNEL(4KB) |
 *	--------------------
 *	|                  |
 *	| OPTEE Log Area   |
 *	| (64kB)           |
 *	|                  |
 * ********************************/
#define TZC_DRAM0_SIZE             (0x02000000) /* 32MB */
#define TZC_DRAM0_BASE             (DRAM0_BASE + (DRAM0_SIZE - TZC_DRAM0_SIZE))

#define TPM_CRB_BASE               0xFED40000
#define TPM_CRB_SIZE               0x1000
#define TPM_TIS_BASE               0xFED40000
#define TPM_TIS_SIZE               0x5000
#define TPM_SMC_TIS_BASE           0x583B0000

#define SCP_TZC_DRAM_SIZE          (0x00200000) /* 2MB */
#define SCP_TZC_DRAM_BASE          (TZC_DRAM0_BASE + (TZC_DRAM0_SIZE - SCP_TZC_DRAM_SIZE))

#define EL3_TZC_DRAM_SIZE          (0x00200000) /* 2MB */
#define EL3_TZC_DRAM_BASE          (SCP_TZC_DRAM_BASE - EL3_TZC_DRAM_SIZE)

#define AP_TZC_DRAM_BASE           (TZC_DRAM0_BASE)
#define AP_TZC_DRAM_SIZE           (TZC_DRAM0_SIZE - SCP_TZC_DRAM_SIZE - EL3_TZC_DRAM_SIZE)

#define OPTEE_SHARE_MEM_SIZE       (0x00400000) /* 4MB */
#define OPTEE_SHARE_MEM_BASE       (TZC_DRAM0_BASE - OPTEE_SHARE_MEM_SIZE)

#define HW_CONFIG_MEM_SIZE         (0x80000) /* 512KB */
#define HW_CONFIG_MEM_BASE         (OPTEE_SHARE_MEM_BASE - HW_CONFIG_MEM_SIZE)

#define ACPI_CHANNEL_BUFF_SIZE     (0x1000)
#define ACPI_CHANNEL_BUFF_BASE     (HW_CONFIG_MEM_BASE - ACPI_CHANNEL_BUFF_SIZE)

#define OPTEE_LOG_SIZE             (0x10000)
#define OPTEE_LOG_BASE             (ACPI_CHANNEL_BUFF_BASE - OPTEE_LOG_SIZE)

#define MEM_RESVED_REGION0_BASE    (OPTEE_LOG_BASE)
#define MEM_RESVED_REGION0_SIZE    (TZC_DRAM0_SIZE + OPTEE_SHARE_MEM_SIZE + HW_CONFIG_MEM_SIZE + ACPI_CHANNEL_BUFF_SIZE + OPTEE_LOG_SIZE)
/***********************************
 *
 * ACPI Channel Reserve sub memory Layout(4KB)
 *
 *      -------------------- TOP
 *      |                  |
 *      |Remainder(3832)   |
 *      --------------------
 *      |EC CMD BUFF  (4)  |
 *      |EC EVENT BUFF(4)  |
 *      --------------------
 *      |                  |
 *      |CHARGER BUFF(128) |
 *      --------------------
 *      |                  |
 *      |UCSI PPM BUFF(128)|
 *      -------------------- BOTTOM
 * ********************************/
#define TYPEC_PPM_BUFF_SIZE        (128)
#define TYPEC_PPM_BUFF_BASE        (ACPI_CHANNEL_BUFF_BASE)
#define CHARGER_EVENT_BUFF_SIZE    (128)
#define CHARGER_EVENT_BUFF_BASE    (TYPEC_PPM_BUFF_BASE + TYPEC_PPM_BUFF_SIZE)
#define EC_BUFF_EVENT_SIZE         (4)
#define EC_BUFF_EVENT_BASE         (CHARGER_EVENT_BUFF_BASE + CHARGER_EVENT_BUFF_SIZE)
#define AP_TO_CM4_CMD_SIZE         (4)
#define AP_TO_CM4_CMD_BASE         (EC_BUFF_EVENT_BASE + EC_BUFF_EVENT_SIZE) 


/***********************************
 *
 * Memory Reserved region for Audio DSP Layout
 *
 *      ----------------------
 *      |                     |
 *      | DSP  RESVED(32MB)   |
 *      --------------------  | DRAM0_BASE
 * ********************************/
#define DSP_RESVED_BASE            DRAM0_BASE
#define DSP_RESVED_SIZE            (0x02000000) /* 32MB */



/***********************************
 *
 * Memory Reserved region for AI NPU Layout
 *
 *      ------------------------
 *      |                     |
 *      | NPU  RESVED(16MB)   |
 *      --------------------  | 
  *      ---------------------|NPU_RESVED_BASE
 *      |                     |
 *      | DSP  RESVED(32MB)   |
 *      --------------------- | DRAM0_BASE
 * ********************************/
#define NPU_RESVED_BASE            (DSP_RESVED_BASE+DSP_RESVED_SIZE)
#define NPU_RESVED_SIZE            (0x01000000) /* 16MB */


/***********************************
 *
 * Memory Protected region for Video  Layout
 *
 *  --------------------------------  DRAM1_BASE+TARGET_DDRSIZE-DRAM0_SIZE
 *  |                              |
 *  | VIDEO Protected(8M+128M+16M) |
 *  -----------------------------  | VIDEO_PROTECTED_BASE
 * ********************************/
#define VIDEO_PROTECTED_SIZE       (0x09800000) /* 152MB */

/***********************************
 *
 * Memory Reserved region for GPU  Layout
 *
 *  --------------------------------  DRAM1_BASE+TARGET_DDRSIZE-DRAM0_SIZE
 *  |                               |
 *  | GPU  RESVED(512M)             |
 *  -----------------------------   | GPU_RESVED_BASE
 * ********************************/
#define GPU_RESVED_SIZE            (0x20000000) /* 512MB */


/***********************************
 *
 * SW INFO Register definie
 * ********************************/
#define SW_INFO_REGISTER_BASE      0x58000000
#define SW_INFO_REGISTER_OFFSET    0x3E0000
#define SW_INFO_REGISTER_SIZE      0x200



/***********************************
 *  
 *  VENG GPU VGA BASE 
 * ********************************/
#ifdef TARGET_MACHINE_ARISE_QEMU
/* qemu platform VGA */
#define VENG_CTRL_BASE             0x53000000
#define VENG_CTRL_SIZE             (0x100000+0x20000)
#define VENG_FB_BASE               0x53120000
#define VENG_FB_SIZE               (8*1024*1024)

#define GTIMER_CNTRL_BASE           0x54800000  /* CNTControlBase - System counter control */
#define GTIMER_READ_BASE            0x54810000  /* CNTReadBase - Read-only counter view */
#define GTIMER_CTL_BASE             0x54000000  /* CNTCTLBase - Timer control (per GTDT) */
#define GTIMER_FRAME0_BASE          0x54010000  /* CNTBase0 - Timer frame 0 (per GTDT) */
#define GTIMER_EL0_FRAME0_BASE      0x54020000  /* CNTEL0Base0 - EL0 view of frame 0 */
#define GTIMER_FRAME_SIZE           0x1000      /* 4KB per frame */
#define INT_GTIMER_FRAME0           280
#define INT_VIC_GTIMER_FRAME0       21
#else
#define VENG_CTRL_BASE             0x58100000
#define VENG_CTRL_SIZE             0x180000
#define VENG_FB_BASE               0
#define VENG_FB_SIZE               0
#endif

/***********************************
 *  
 *  VMM ENGINE SUBSYS 
 * ********************************/
#define VMM_ENGINE_BASE             0x58400000
#define VMM_ENGINE_SIZE             0x400000
#define VMM_CTRL_BASE               NOC_MMIO_REG_BASE
#define VMM_CTRL_SIZE               0x110000

/***********************************
 *
 * DDR Controller Register definie
 *     Each space is the same size
 * ********************************/
#define OMC_REGISTER_BASE0_0       0x51120000
#define OMC_REGISTER_BASE0_1       0x51130000
#define OMC_REGISTER_BASE1_0       0x51140000
#define OMC_REGISTER_BASE1_1       0x51150000
#define OMC_REGISTER_SIZE          0x10000   

#define FB_CHI_ID_CTRL             0x58316100

/***********************************
 *
 * DDR PHY Register definie
 *      Each space is the same size
 * ********************************/
#define PHY_REGISTER_BASE0_0       0x51160000
#define PHY_REGISTER_BASE0_1       0x51170000
#define PHY_REGISTER_BASE1_0       0x51180000
#define PHY_REGISTER_BASE1_1       0x51190000
#define PHY_REGISTER_SIZE          0x10000

/*
 * Common Defines for HAPS
 */

#if (defined(TARGET_MACHINE_ARISE_HAPS) || defined(TARGET_MACHINE_ARISE_HAPS80))
#define BASE_CLOCK                 (8 * 1000000)
#define MSHC_CLOCK                 (20 * 1000000)
/*
 * stability: 1bit@10M > 1bit@20M > 4bit@5M > 8bit@5M
 */
#define MSHC_MAX_CARD_CLK          (10 * 1000000)
#define EMMC_MAX_BUS_MODE          1
/* Max 8bit@5M stable for Boot Mode */
#define EMMC_BOOT_MODE_CARD_CLK    (5 * 1000000)
#define EMMC_BOOT_MODE_BUS_WIDTH   8
#define UART_DLF_VAL               0x1A
#else
#define BASE_CLOCK                 (24 * 1000000)
#define BASE_CM4_CLOCK             (250 * 1000000)
#define MSHC_CLOCK                 (200 * 1000000)
#define MSHC_MAX_CARD_CLK          (200 * 1000000)
#define EMMC_MAX_BUS_MODE          8
#define EMMC_BOOT_MODE_BUS_WIDTH   8
#define UART_DLF_VAL               0x0
#endif

#ifdef TARGET_MACHINE_ARISE_QT
#define CONSOLE_BAUDRATE           1500000
#else
#define CONSOLE_BAUDRATE           115200
#endif

#define UART_CLOCK                 BASE_CLOCK
#define SYS_COUNTER_CLK            BASE_CLOCK

/*
 * Misc Registers
 */
#define EMMC_PRIVATE_REG0          0x50390064
#define EMMC_PRIVATE_REG1          0x50430068
#define VSOC_WDT_SEC_MISC_REG0     0x60530000

#define VSUS_DBG_COUNT0_REG        0x503f0000
#define VSUS_DBG_COUNT1_REG        0x503f0100
#define VSUS_DBG_COUNT2_REG        0x503f0200
#define VSUS_DBG_COUNT3_REG        0x503f0300
#define VSOC_DBG_COUNT0_REG        0x604f0000
#define VSOC_DBG_COUNT1_REG        0x604f0100
#define VSOC_DBG_COUNT2_REG        0x604f0200
#define VSOC_DBG_COUNT3_REG        0x604f0300
#define VSOC_DBG_COUNT4_REG        0x604f0400

#define SUSMMU_TE_HOST0_ID         0x50410000
#define SUSMMU_TE_HOST1_ID         0x50410004
#define SUSMMU_TE_HOST2_ID         0x50410008
#define SUSMMU_TE_HOST3_ID         0x5041000c
#define BMMU_USB30_ID              0x50410010
#define BMMU_USB31_ID              0x50410014
#define BMMU_USB20_ID              0x50410018
#define BMMU_USB21_ID              0x5041001c
#define BMMU_USB22_ID              0x50410020
#define BMMU_GMAC0_ID              0x50410024
#define BMMU_GMAC1_ID              0x50410028
#define BMMU_GMAC2_ID              0x5041002c
#define BMMU_SDIO_ID               0x50410030
#define BMMU_SD_ID                 0x50410034
#define BMMU_EMMC_ID               0x50410038
#define BMMU_SATA0_ID              0x60500000
#define BMMU_SATA1_ID              0x60500004
#define BMMU_DMA3_ID               0x60500008

#define MISC_NS_BASE               0x60400000
#define NS_MISC_APB_BASE           0x58310000
/*
 * NIC-400 Boot Secure Switch registers
 */
#define SUSAPB0_NIC_SECURITY_REG   0x50800100
#define SOCAPB0_NIC_SECURITY_REG   0x60600104
#define SUSAPB1_NIC_SECURITY_REG   0x50A00100
#define SUSAHB0_NIC_SECURITY_REG   0x500000D4

/************************
* Used By QEMU
*************************/
#define SMMU_BASE                  SUSMMU_BASE
#define SMMU_SIZE                  SUSMMU_SIZE
#define BMMU_BASE                  BMMMU_BASE
#define BMMU_SIZE                  BMMMU_SIZE
#define QEMU_VIRT_IRQ              232
#define QEMU_VIRT_IRQ_SIZE         QEMU_VIRT_NUM 

/******************************
* Mailbox NS Channel Define
*******************************/
#define MB_NS_SLOT_LOW_A2P         0
#define MB_NS_SLOT_HIGH_A2P        (MB_NS_SLOT_LOW_A2P+1)
#define MB_NS_SLOT_HIGH_P2A        (MB_NS_SLOT_HIGH_A2P+1)
#define MB_NS_SLOT_TYPE_C          5
#define MB_NS_SLOT_CHARGER         (MB_NS_SLOT_TYPE_C+1)
#define MB_NS_SLOT_CPPC_BIG        (MB_NS_SLOT_CHARGER+1)
#define MB_NS_SLOT_CPPC_LITTLE     (MB_NS_SLOT_CPPC_BIG+1)
#define MB_NS_SLOT_THEM_SENSOR_BIG     (MB_NS_SLOT_CPPC_LITTLE+1)
#define MB_NS_SLOT_THEM_SENSOR_LITTLE     (MB_NS_SLOT_THEM_SENSOR_BIG+1)
#define MB_NS_SLOT_THEM_SENSOR_FAN     (MB_NS_SLOT_THEM_SENSOR_LITTLE+1)
#define MB_NS_SLOT_EC              (MB_NS_SLOT_THEM_SENSOR_FAN+1)

/****************************************
* DVFS PMIC  Define
*****************************************/
#define DSU0_BIG0_I2C_ADDR       0x50
#define DSU0_BIG1_I2C_ADDR       0x51
#define DSU1_LITTLE0_I2C_ADDR    0x50
#define DSU1_LITTLE1_I2C_ADDR    0x51
#define DSU0_I2C_REG_ADDR        0x5D
#define DSU1_I2C_REG_ADDR        0x5E

/*******CPU Freq table in HZ**************/
#define DSU0_FREQ_LEVEL0         400000000
#define DSU0_FREQ_LEVEL1         800000000
#define DSU0_FREQ_LEVEL2         914280000
#define DSU0_FREQ_LEVEL3         1066660000
#define DSU0_FREQ_LEVEL4         1280000000
#define DSU0_FREQ_LEVEL5         1600000000
#define DSU0_FREQ_LEVEL6         2133000000
#define DSU0_FREQ_LEVEL7         3200000000

#define DSU1_FREQ_LEVEL0         300000000
#define DSU1_FREQ_LEVEL1         600000000
#define DSU1_FREQ_LEVEL2         685710000
#define DSU1_FREQ_LEVEL3         800000000
#define DSU1_FREQ_LEVEL4         960000000
#define DSU1_FREQ_LEVEL5         1200000000
#define DSU1_FREQ_LEVEL6         1600000000
#define DSU1_FREQ_LEVEL7         2400000000

/*****CPU Voltage table in microvlot******/
#define DSU0_MICRO_VOLT_LEVEL0   1000000
#define DSU0_MICRO_VOLT_LEVEL1   1000000
#define DSU0_MICRO_VOLT_LEVEL2   1012500
#define DSU0_MICRO_VOLT_LEVEL3   1012500
#define DSU0_MICRO_VOLT_LEVEL4   1037500
#define DSU0_MICRO_VOLT_LEVEL5   1050000
#define DSU0_MICRO_VOLT_LEVEL6   1062500
#define DSU0_MICRO_VOLT_LEVEL7   1075000

#define DSU1_MICRO_VOLT_LEVEL0   575000
#define DSU1_MICRO_VOLT_LEVEL1   575000
#define DSU1_MICRO_VOLT_LEVEL2   587500
#define DSU1_MICRO_VOLT_LEVEL3   600000
#define DSU1_MICRO_VOLT_LEVEL4   612500
#define DSU1_MICRO_VOLT_LEVEL5   625000
#define DSU1_MICRO_VOLT_LEVEL6   637500
#define DSU1_MICRO_VOLT_LEVEL7   650000

/*the volt value must correspond to opp freq level*/
#define DSU0_VOLT_TAB_LEVEL0     0x1
#define DSU0_VOLT_TAB_LEVEL1     0x2
#define DSU0_VOLT_TAB_LEVEL2     0x3
#define DSU0_VOLT_TAB_LEVEL3     0x4
#define DSU0_VOLT_TAB_LEVEL4     0x5
#define DSU0_VOLT_TAB_LEVEL5     0x6
#define DSU0_VOLT_TAB_LEVEL6     0x7
#define DSU0_VOLT_TAB_LEVEL7     0x8

#define DSU1_VOLT_TAB_LEVEL0     0x1
#define DSU1_VOLT_TAB_LEVEL1     0x2
#define DSU1_VOLT_TAB_LEVEL2     0x3
#define DSU1_VOLT_TAB_LEVEL3     0x4
#define DSU1_VOLT_TAB_LEVEL4     0x5
#define DSU1_VOLT_TAB_LEVEL5     0x6
#define DSU1_VOLT_TAB_LEVEL6     0x7
#define DSU1_VOLT_TAB_LEVEL7     0x8

/*****Thermal Sensor TMP0804******/
#define  D_OTP_25               285
#define  D_OTP_SL               5
#define  TEMP_NORMAL			30
#define  TEMP_MIDDLE			70
#define  TEMP_HIGH				90

#endif   /* __ARISE2_SOC_HW_CONFIG */
